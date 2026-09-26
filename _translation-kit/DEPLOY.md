# Moving library.misbah-inc.com to S3 + CloudFront

**Nothing about GitHub changes except that it stops being the web server.** The repo, the
history, GitHub Desktop and your commit-and-push stay as they are. AWS only holds a copy
of the finished site and hands it to readers.

**Your DNS does not move.** `misbah-inc.com` is registered at Wix, its nameservers are
Wix's, and that zone also carries the Wix company site and Google Workspace mail. We
change **one CNAME** — the same kind of record you already added for GitHub. Wix, your
website and your email are untouched.

## Why leave GitHub Pages

| | GitHub Pages | S3 + CloudFront |
|---|---|---|
| Published site size | **1 GB hard**, every plan | no limit |
| Files | no limit | no limit |
| Deploy | **times out after 10 min**, rebuilds the whole site | uploads only what changed |
| Cache headers | not settable | per file type |
| Private repo | needs a paid GitHub plan | irrelevant — no repo is read |

The library is ~0.52 GB and ~48,600 files in Arabic alone. It passes 1 GB at its first
Bihar translation, and the 10-minute ceiling already applies to *every* future deploy.

---

## Architecture: private bucket, not public

An earlier draft of this file used S3's **static website endpoint**, which resolves
`/bihar/4/50/` to `bihar/4/50/index.html` for free but **requires the bucket to be
public**. That is the simpler build and it is the wrong trade:

- A public bucket has its own reachable URL. Anyone who finds it can pull all 48,600
  files **straight from S3, bypassing CloudFront** — billed as S3 egress (~$0.09/GB)
  instead of CloudFront's free tier. It is a real cost-exposure path, not just posture.
- CloudFront caching, compression and any future WAF rule are bypassed with it.

So: **bucket private, reachable only by CloudFront via Origin Access Control (OAC).**
The price of that is that the REST endpoint has no directory-index behaviour, so a small
**CloudFront Function** maps directory URLs onto `index.html`. It is ten lines and it is
tested before DNS moves.

---

## Two kinds of setup: account-level vs machine-level

This distinction matters because the owner may change laptop, and other people work on
the library from their own machines through the shared Drive folder.

**Done ONCE for the account, by anyone, ever** — steps 3 to 6 below. The bucket, the IAM
policy, the certificate, the distribution and the URL function live in AWS, not on a
computer. A new laptop does not repeat them, and a new teammate does not repeat them.

**Done ONCE PER MACHINE, by each person who publishes** — step 2 below:

1. Install the AWS CLI on that machine.
2. Run `aws configure` with **that person's own** access key.
3. Have the Library folder, which Google Drive already provides.

That is the whole of it. The publish command is identical everywhere:

```bash
python _translation-kit/deploy_s3.py --bucket library-misbah-inc --dist E1234ABCDEF
```

### New laptop, same person

Install the CLI, run `aws configure` with the same key, done. Nothing in AWS changes.
If the old laptop is being retired or sold, delete that access key in **IAM → Users →
library-deploy → Security credentials** and create a fresh one — a key on a machine you
no longer control is a key you no longer control.

### New person who needs to publish

Give them **their own IAM user**, never a copy of someone else's key:

1. **IAM → Users → Create user**, e.g. `library-deploy-ali`, no console access.
2. Attach the **same** `library-deploy-policy` created in step 4.
3. They create their own access key and run `aws configure` on their machine.

One user each, rather than a shared key, because it means a single person can be revoked
without disturbing anyone else, CloudTrail shows who published what, and nobody has to
rotate everyone's credentials when one person leaves.

### What must never go on Google Drive

The credentials file — `C:\Users\<name>\.aws\credentials` — or the access key in any
other form. It belongs on the individual machine. Put it in the shared folder and
everyone with access to that folder can publish to the live site, and the key is exposed
to everyone the folder is ever shared with afterwards.

The AWS CLI installer itself is harmless — a public download containing no credentials —
but there is no reason to keep it on Drive either.

---

## Day-to-day: publishing a change

The files never move. They stay in `G:\My Drive\Misbah Library\Library`, edited there
by whoever is working, exactly as before.

What changed is that **pushing to GitHub no longer publishes the site.** Under GitHub
Pages one gesture did two jobs; now they are separate:

| | Before | Now |
|---|---|---|
| Save the work, with history | `git push` | `git push` — unchanged |
| Put it in front of readers | *also* `git push` | `deploy_s3.py` |

So a normal change is:

1. Edit the files on Drive (or have Claude build them).
2. **Rebuild the search indexes** if any reading page changed:

   ```bash
   python _translation-kit/build_search_index.py --all
   ```

   These are the files a reader's browser downloads when they use the **Search**
   button inside a book. They are deliberately **not in git** — they are a second
   copy of every book's text, about 165 MB, and the repository is already hard to
   push. `aws s3 sync` does not read `.gitignore`, so they still reach S3.

   The consequence to know about: **on a machine that has never run this, the
   indexes do not exist**, and `deploy_s3.py`'s `--delete` would remove them from
   the bucket — every Search button would start answering "Could not load." The
   deploy script refuses to run in that state rather than let it happen, and tells
   you this command. It checks per volume, so a stale `bihar/assets/search-index.json`
   does not fool it.

3. **Publish:**

   ```bash
   python _translation-kit/deploy_s3.py --bucket library-misbah-inc --dist E2P6OCWDH7403J
   ```

   It compares local against the bucket, uploads only what differs, and invalidates the

   **For a change that only ADDS or UPDATES known paths — a new book, a
   rebuilt index — use `--only` instead, and expect minutes rather than
   hours:**

   ```
   python _translation-kit/deploy_s3.py --bucket library-misbah-inc \
          --dist E2P6OCWDH7403J \
          --only burhan --only assets/search \
          --only sitemap-2.xml --only catalog.json
   ```

   The default sync stats EVERY file in the tree to decide what changed.
   Measured on the البرهان deploy, from this Google Drive folder:
   **3,526,796 metadata operations** across ~65,000 files — about 54 per file
   — **67 minutes elapsed for 370 seconds of CPU**, so 91% of the time was
   spent waiting on Drive. That price is paid in full whether one page changed
   or four thousand, and it rises with every book published: the tree was
   ~48,600 files when this document was written and is ~65,000 now.

   `--only` walks just the paths named — 4,354 files for a book instead of
   65,000 — and invalidates just those prefixes (a directory as `/burhan/*`, a
   single file as `/sitemap-2.xml`). Each path counts as one against the
   1,000-a-month free allowance, so a handful costs what the blanket `/*` does.

   > **`--only` never passes `--delete`, so it cannot remove anything.**
   > Anything that DELETES or RENAMES a file must go through the default
   > whole-site sync — it is the only mode that can notice something
   > disappeared. When in doubt, use the default and wait.
   CDN.

   **A full deploy takes about 50 minutes, and that is Google Drive, not AWS.**
   Measured on 2026-09-22: 170 MB of new search indexes uploaded in *under a minute*,
   and unchanged pages were correctly skipped — but `aws s3 sync` must still stat all
   53,000 local files to work out what changed, and every one of those is a network
   round trip to a streamed Drive folder. Everything that walks this tree costs the
   same: `verify_pagers.py` ~50 min, building Bihar's indexes 28 min.

   **So for a routine change, sync only what changed** — seconds instead of an hour,
   because it only walks that subtree:

   ```bash
   aws s3 sync "G:/My Drive/Misbah Library/Library/kafi" s3://library-misbah-inc/kafi      --cache-control public,max-age=600 --only-show-errors
   aws cloudfront create-invalidation --distribution-id E2P6OCWDH7403J --paths "/kafi/*"
   ```

   Note there is no `--delete` there: a targeted sync cannot safely delete, because it
   has no view of the rest of the site. Run the full `deploy_s3.py` when pages have been
   *removed*, or every so often as a reconciliation pass.

   **The durable fix is to stop streaming the files.** Marking the Drive folder
   "Available offline" pins real files to local disk, and would speed up the deploy, the
   index builds, the verifiers — and very likely the git push failures, which were the
   same Drive-streaming problem wearing a different hat.

4. **Commit and push** to GitHub as usual — that is now purely the archive and history.
   The search indexes are skipped automatically; nothing to do.

> **Adding a pattern to `EXCLUDE` does not remove what is already in the bucket.**
> `aws s3 sync --delete` applies its filters to the *destination* listing too, so an
> excluded key is invisible to the delete pass rather than deleted by it. `.claude/launch.json`
> was live on the site and survived a deploy that excluded it. Clear such things once, by hand:
>
> ```bash
> aws s3 rm s3://library-misbah-inc/.claude/ --recursive
> aws cloudfront create-invalidation --distribution-id E2P6OCWDH7403J --paths "/.claude/*"
> ```

The order does not matter, and neither does doing both in the same sitting. They are
independent: the deploy decides what readers see, the push decides what is recorded.

**Before publishing anything that adds or rebuilds pages**, the existing rules still
apply — `verify_pagers.py` must report 0 broken links, `gen_sitemap.py` must be re-run,
and `build_search_index.py` must be re-run for the books that changed.
See `CLAUDE.md`, "Page addition checklist".

### Restoring the single gesture, if it is ever wanted

A GitHub Action can run the deploy on every push, making `git push` publish again. It
needs the AWS key stored as a GitHub secret — or better, OIDC, so no key is stored at
all. Claude can write the workflow file; the owner commits it, since Claude never touches
GitHub. Not needed while publishing is a command someone runs deliberately.

## Step 1 — AWS account (10 min)

1. Create an account at <https://aws.amazon.com/>. It needs a card.
2. **Secure the root account first:** top-right menu → **Security credentials** →
   **Assign MFA device**. Use an authenticator app. Then never log in as root for daily
   work — everything below uses a separate user.
3. Search **Billing → Budgets → Create budget** → template → **$5 monthly cost budget**,
   with your email.

   > A budget is an **alert, not a cap.** AWS has no hard spending limit, and
   > notifications can arrive hours after a threshold is crossed. What actually bounds
   > your exposure here is the architecture: static files, no compute, no database, and
   > a private origin that cannot be drained directly.

## Step 2 — AWS CLI (3 min)

Install <https://awscli.amazonaws.com/AWSCLIV2.msi>, then in a **new** terminal:

```bash
aws --version
```

## Step 3 — The bucket, private (5 min)

1. **S3 → Create bucket.** Name `library-misbah-inc`, region `us-east-1`.
2. **Leave "Block all public access" ticked.** Unlike the earlier draft, this bucket stays
   private; CloudFront will be granted access in step 6.
3. Create it. Do **not** enable static website hosting — with OAC it is not used, and
   enabling it would create exactly the public path we are avoiding.

## Step 4 — A least-privilege deploy user (5 min)

**IAM → Users → Create user** (`library-deploy`), no console access.

Attach an inline policy — this grants publishing and nothing else. It cannot delete the
bucket, change its policy, or touch any other AWS service:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": "arn:aws:s3:::library-misbah-inc" },
    { "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::library-misbah-inc/*" },
    { "Effect": "Allow",
      "Action": ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"],
      "Resource": "*" }
  ]
}
```

Then **Security credentials → Create access key → Command Line Interface**, and:

```bash
aws configure
```

Region `us-east-1`, output `json`.

> **Never paste the secret key into a chat, including to me.** `aws configure` stores it
> on your machine and the deploy reads it from there.
>
> If this is ever automated through GitHub Actions, switch to **OIDC** so no key is
> stored anywhere. That is the right answer for automation; it is disproportionate for a
> command you run by hand.

## Step 5 — Certificate (5 min + wait)

1. **Certificate Manager** — confirm the region says **N. Virginia (us-east-1)**.
   CloudFront accepts certificates only from that region, whatever region the bucket is in.
2. Request a public certificate for `library.misbah-inc.com`, DNS validation.
3. It shows one CNAME name/value. Add it at **Wix → Domains → DNS records**.
4. Wait for **Issued**.

## Step 6 — CloudFront, with OAC and the URL function (15 min)

1. **CloudFront → Create distribution.**
2. **Origin domain:** choose the bucket `library-misbah-inc.s3.amazonaws.com` from the
   dropdown (the REST endpoint — correct *because* we are using OAC).
3. **Origin access:** *Origin access control settings* → **Create new OAC** → accept the
   defaults → then CloudFront shows a bucket policy to copy. **Copy it**, go to
   **S3 → bucket → Permissions → Bucket policy**, paste, save. This is what lets
   CloudFront — and only CloudFront — read the bucket.
4. **Viewer protocol policy:** Redirect HTTP to HTTPS
5. **Compress objects automatically:** Yes
6. **Alternate domain name (CNAME):** `library.misbah-inc.com`; **Custom SSL certificate:**
   the one from step 5
7. **Default root object:** `index.html`
8. Create the distribution, then add the URL function:
   **CloudFront → Functions → Create function**, name `rewrite-index`, runtime
   `cloudfront-js-2.0`, paste:

```js
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // "/bihar/4/50/" -> "/bihar/4/50/index.html"
    if (uri.endsWith('/')) {
        request.uri = uri + 'index.html';
        return request;
    }
    // "/bihar/4/50" -> 301 to "/bihar/4/50/". Every canonical URL, sitemap entry and
    // internal link on this site ends in a slash, so redirecting rather than serving
    // keeps one address per page instead of two with identical content.
    if (!uri.split('/').pop().includes('.')) {
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: { location: { value: uri + '/' } }
        };
    }
    return request;
}
```

   **Publish** it, then **Associate** → your distribution → *Default (\*)* behaviour →
   event type **Viewer request**.

9. **Error pages** (the REST endpoint returns 403, not 404, for a missing key):
   **Distribution → Error pages → Create custom error response**, twice —
   for **403** and for **404**: response page `/404.html`, HTTP response code **404**.

10. Note the distribution's **ID** (`E1234ABCDEF`) and **domain name**
    (`dxxxxxxxx.cloudfront.net`). Wait for Status **Enabled**.

---

## ⏸ Stop and send me the bucket name, distribution ID and distribution domain.

None of those are secret. Then I upload and verify.

---

## Step 7 — me: upload and verify

```bash
python _translation-kit/deploy_s3.py --bucket library-misbah-inc --dist E1234ABCDEF --dry-run
python _translation-kit/deploy_s3.py --bucket library-misbah-inc --dist E1234ABCDEF
```

The first upload reads ~48,600 files off Google Drive, so expect it to be slow **once**.

I then verify on `dxxxxxxxx.cloudfront.net` before any DNS change: all four language
trees, language switching, the contents drawer, pagers, the `fm-` pages, volume 83's
edition notice, a deliberate 404, sitemap and robots. **Your live site keeps serving from
GitHub Pages throughout.**

## Step 8 — you: the switch (2 min)

**Wix → DNS records** → change the `library` CNAME from `misbah-inc.github.io` to
`dxxxxxxxx.cloudfront.net`. Nothing else in the zone changes.

**Rollback:** point it back at `misbah-inc.github.io`.

## Step 9 — afterwards, in this order

1. **Leave GitHub Pages enabled for now.** It is your rollback while DNS settles.
2. After a few days of the new site behaving, GitHub → **Settings → Pages → disable**.
   This is what removes the 10-minute deploy ceiling.
3. **Then** commit the Bihar volumes — pause Google Drive syncing first (tray icon),
   commit, resume, to avoid the rename wedge described in `CLAUDE.md`.
4. Optionally make the repo private. Nothing reads it any more.
5. Search Console needs nothing: same domain, same URLs, same `/sitemap.xml`.

---

## What it actually costs

| Line | At this size |
|---|---|
| S3 storage, 0.52 GB × $0.023/GB | **$0.012 / month** |
| S3 PUT requests, full re-upload (48,600 × $0.005/1,000) | **$0.24, one-off**; later deploys upload only changes |
| S3 GET from CloudFront | pennies; CloudFront caches |
| CloudFront delivery | free-tier allowance covers a library of this traffic |
| Certificate, DNS | $0 — ACM is free, DNS stays at Wix |

Normal operation is **well under $1/month**, but that is an estimate, not a guarantee —
traffic is the variable. Check the actual bill after the first full month rather than
trusting this table. The $5 budget alert exists for exactly that reason.

## What the deploy script does that a bare `aws s3 sync` does not

- **Does not publish `_translation-kit/` (192 MB), `CLAUDE.md`, `CHANGELOG.md` or any
  script.** All are served on the live site today; once the repo is private, publishing
  them would leak exactly what was closed. `--delete` means running it against a bucket
  that already has them **removes** them.
- **Cache headers per file type** — fonts a year, css/js a day, pages ten minutes.
- **One CloudFront invalidation per deploy.** A `/*` wildcard is a single path against
  the 1,000/month free allowance, so a changed `reader.js` reaches everyone at once. This
  is the real answer to the problem `ASSETS_V` was invented for.
