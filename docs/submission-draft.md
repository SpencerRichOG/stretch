# Stretch submission draft (Track 1)

For the team. This is a draft only. Nothing has been submitted.

This repository is public. Keep only placeholders in this file. Type the real team name, member names and emails into the submission form (or the submit command in your terminal), never into this file.

## Fields

| Field | Value | Limit and check |
| --- | --- | --- |
| Track | Track 1, Skills | |
| Team name | [TEAM NAME] | up to 60 characters |
| Project name | Stretch | up to 60 characters; 7 |
| One-liner | Stretch finds every dollar you're wasting in college (food, subscriptions, parking, gear) and plans your week so you keep it. | up to 140 characters; 125, checked with a script |
| Member 1 | [NAME] <[EMAIL]> | 1 to 4 members, distinct emails |
| Member 2 | [NAME] <[EMAIL]> | optional |
| Member 3 | [NAME] <[EMAIL]> | optional |
| Skill link | https://github.com/SpencerRichOG/stretch | the repository link, not a branch link and not a pinned commit |
| Platform | [tiktok or instagram] | optional; only TikTok or Instagram |
| Post link | [https://www.tiktok.com/... or https://www.instagram.com/reel/...] | optional; must be https:// and on the platform picked |

Public on the gallery: team name, project name, one-liner and links. Member emails stay private.

This resolves the open question in docs/BUILD-NOTES.md: the kit's rules.md and cubbie-testing.md both say to submit the repository link.

## Before submitting

1. Everything is merged to main and pushed. Cubbie installs the newest commit of the default branch from the repository link.
2. The repository is public.
3. The validator passes on main: `python C:\Users\lafsd\code\cubbie-hackathon-kit\skills\cubbie-skill-creator\scripts\validate_cubbie_skill.py <repo folder>`.
4. The Skill installed from the link on a real Cubbie, and the main flow ("I have $41 until Friday and nothing in my fridge") worked.
5. Check the Track 1 close time with the kit's `status` command, or on hackathon.cubbie.ai or the organizers' Discord. Assume the earliest time until it is confirmed.

## How to submit (Lucas runs this; preview first)

From the kit's cubbie-hackathon skill folder: `status`, `login`, `whoami`, `mine`, then `submit` without `--yes` to see the preview. Read the preview. Only then run the same command with `--yes`. If the preview says it starts a new entry but the team already has one, stop: you are signed in with a different address.

```powershell
python scripts/hackathon.py submit --track skills --team "[TEAM NAME]" --name "Stretch" `
  --pitch "Stretch finds every dollar you're wasting in college (food, subscriptions, parking, gear) and plans your week so you keep it." `
  --member "[NAME] <[EMAIL]>" `
  --repo https://github.com/SpencerRichOG/stretch
```

Add `--platform tiktok --post <link>` (or instagram) when the post is up; that can also be added later with the same submit command. Extra posts (up to 5) go in with `posts --track skills --add <link>`.
