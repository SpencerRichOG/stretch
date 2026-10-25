# Stretch demo video plan

For the team, not for Cubbie. This is the plan for the main 30 to 45 second vertical video (TikTok or Instagram), plus 5 cut-downs. It replaces the script in the spec's Section 7.

Changes from the spec:
- The 20-26 s DashPass shot is gone. perks.md forbids saying a student gets DashPass free or qualifies for it. That shot now shows the Spotify student finding.
- The 33-40 s "job survey" is gone because it isn't built. That shot now shows the gear tip and the subscription audit.
- The end card's "DoorDash, let's make it one tap" line is gone, because it suggests a tie to a company we have no deal with.
- The 10-20 s plan uses no fixed numbers. Fill [TOTAL], [BUDGET] and [DAYS] from Cubbie's real reply in your recording.

## 1. Shot list

| Time | Shot | On-screen text | Voiceover |
| --- | --- | --- | --- |
| 0-3 s | [ON-CAMERA PERSON: Lucas decides; must be a real person, no AI avatar], real fridge or dorm: opens a near-empty fridge, looks at their phone. Show no bank app and no real balance. | "$41 until Friday." | "41 dollars until Friday. Nothing in the fridge." |
| 3-10 s | Screen recording: the student types to Cubbie "I have $41 until Friday and nothing in my fridge." and sends it. | "So I texted Cubbie." | "So I texted Cubbie." |
| 10-20 s | Screen recording: Stretch's reply scrolls in (this week's deals, the prep plan, the total). Zoom in on the total line. | "[TOTAL] / [BUDGET]" then "[DAYS] days of food" | "It found this week's deals near campus and planned [DAYS] days of food for [TOTAL]." |
| 20-26 s | Screen recording: the perks reply line "Spotify student plan: $6.99/mo vs $12.99, saves about $72/yr." Zoom in on it. | "+ about $72/yr" | "Then it flagged Spotify: the student plan is $6.99 vs $12.99, about 72 bucks a year." |
| 26-33 s | Screen recording: the student replies "1" and the cart fills in Cubbie's browser. Stop before checkout. **Fallback** if Walmart.com shows a bot check: show Stretch's shopping-list reply instead. | "You just tap pay." (fallback: "List's ready. You just shop.") | "I reply 1, and the cart fills itself. I still pay." |
| 33-40 s | Quick cuts, about 3 s each: (a) the gear reply ("is a rice cooker worth it", with its payback line); (b) the subscription audit's top 3 list. | "Every Sunday. 2 minutes." | "Kitchen gear that pays for itself. Subscriptions you forgot about. Every Sunday, two minutes." |
| 40-45 s | End card (see section 6). | End card text | "Stretch. Text the link to Cubbie." |

Rule for every number: what's on screen must be exactly what Cubbie said in that recording. If Cubbie's reply says "$38.40 for 6 days", the overlay says "$38.40 / $41" and "6 days". The day count depends on the weekday you record (a Saturday "until Friday" is not a Tuesday "until Friday"), so take [DAYS] from the reply and never from this script. If the Spotify line in the reply differs from "$6.99 vs $12.99, about $72/yr", use what the reply says.

## 2. Recording checklist (iPhone, iMessage)

Before recording:
1. Use a test Cubbie conversation with made-up data only. Do not connect a real Gmail. When Stretch asks to connect Gmail, decline and type the subscriptions (Stretch supports this). No real inbox appears at any point.
2. Install the Skill from the repository link and finish setup off camera, so take 1 goes straight to a plan (see section 3).
3. Hero kitchen: "microwave, stove, pan and pot". Pan recipes need a stove, so a pan-and-microwave kitchen may get no chicken plan. Run take 1 once off camera to check that it gives a full plan.
   Rerun the plan right before recording: weekly ads change, so the total and the "Real prices" line can differ from any earlier run. Use only the numbers in the recorded reply.
4. Turn on Do Not Disturb (Control Center > Focus > Do Not Disturb). Clear all notifications. Turn off message previews for other apps if any still come through.
5. Close other apps. Check the screen for: other iMessage threads, contact names, your phone number, email addresses, real bank or card apps, location, photos. None of these may appear.
6. Settings > Display & Brightness > Text Size: bump it up one or two steps so replies are readable on a phone screen.
7. Charge above 50 percent (a low-battery banner ruins a take). Set the screen to stay on (Auto-Lock: Never) while recording, and set it back afterwards.
8. Add Screen Recording to Control Center if it isn't there. Keep the microphone off; record the voiceover separately.

While recording:
9. Start the screen recording, wait 1 second, send the text, let the full reply arrive, wait 2 seconds, then stop.
10. Do one take per text in section 3. Re-record any take where Cubbie's reply is wrong or too long. Do not edit Cubbie's words.
11. For the cart take: stop recording before any sign-in, address or payment screen. Nobody pays on camera.
12. Hook shot (0-3 s): film [ON-CAMERA PERSON] (a real person, never an AI avatar) and a real fridge or dorm, vertical, in good light. Nothing generated.

After recording:
13. Watch every clip frame by frame for anything sensitive. Crop or blur it, or re-record.
14. Write down the exact [TOTAL], [BUDGET] and [DAYS] from the reply. Use those in the overlays.
15. Hand the clips and numbers to whoever edits (Person 2 posts).

## 3. Texts to send Cubbie, in order

Setup (off camera, made-up student):
1. `https://github.com/SpencerRichOG/stretch`
2. `yes` (lets Cubbie fetch and install the Skill)
3. In a new message: `set up Stretch`
4. Answer setup questions with the made-up profile: ASU Tempe, dorm, ZIP 85281, no car, ALDI, Target, Fry's and Safeway (the stores with real weekly-ad prices near ASU; cart site Walmart.com), kitchen `microwave, stove, pan and pot`, no diet limits, weekly food budget $41, Sunday check-in at 6 pm Arizona time.
5. When asked to connect Gmail: `no thanks, I'll type them`, then `Spotify Premium $12.99 a month, an AI chatbot plan $20 a month, and a gym near campus $30 a month`

Takes (on camera, each in a new message):
- Take 1 (3-20 s): `I have $41 until Friday and nothing in my fridge`
- Take 2 (26-33 s): `1` (only if the reply offered "1" for the cart; otherwise reply with the number it gave for the cart or list)
- Take 3 (20-26 s and 33-40 s audit): `am I wasting money on subscriptions?`
- Take 4 (33-40 s gear): `is a rice cooker worth it for my dorm?`
- Take 5 (optional, for the "every Sunday" cut-down): accept the Sunday check-in when Stretch offers it, and record the confirmation.

## 4. Captions and hashtags

TikTok:
> $41 until Friday and an empty fridge, so I texted Cubbie. Stretch planned my week from this week's deals and flagged Spotify: the student plan is $6.99 vs $12.99. A Cubbie Skill, link in bio.
> #college #collegelife #brokecollegestudent #mealprep #budgeting #studentdiscount #asu #sundevils #cubbie

Instagram (Reels):
> $41 until Friday. Empty fridge. One text. Stretch is a Cubbie Skill that plans a week of food from this week's deals and finds student perks you aren't using. Text the link to your Cubbie (link in bio).
> #collegelife #collegebudget #mealprep #studentlife #studentdiscount #asu #sundevils #savemoney #cubbie

Put https://github.com/SpencerRichOG/stretch in the bio or first comment. Any number in a caption must match the video.

Cut-down ideas (up to 5 extra posts, each 10 to 20 s):
1. Gear tip: "Is a rice cooker worth it in a dorm?" Show Stretch's payback reply and the number it gives.
2. Subscription audit: "I asked Cubbie if I'm wasting money on subscriptions." Show the top 3 list as Cubbie sent it.
3. "$41 until Friday": the hook and the plan only, with [TOTAL] / [BUDGET] from the real reply.
4. ASU free perks: "Things ASU already gives you for free": the gym with your ID, ChatGPT Edu, game tickets. Wording from perks.md only, with a link to the source page in the caption.
5. "Every Sunday, 2 minutes": the Sunday check-in arriving and the student replying "1".

## 5. Honesty rules

1. Numbers on screen, in voiceover and in captions match what Cubbie said in the recording. No rounding up, no "saves $500/yr" claims.
2. The hook shot (a real person, real fridge or dorm) and every screen recording are real. Never generate them.
3. No AI avatars standing in for students.
4. Any realistic AI-generated footage (b-roll) gets the platform's AI label (TikTok: "AI-generated content" toggle; Instagram: "AI info" label). Auto-captions, jump cuts and music need no label.
5. No fake receipts, order confirmations or account screenshots, real brand or not. Subscriptions are typed in the chat.
6. Say "about" for prices, as Cubbie does. No promise that a viewer qualifies for any student plan.
7. Show no real names, emails, phone numbers, bank or card information.

## 6. End card

> Stretch
> Text the link to your Cubbie.
> https://github.com/SpencerRichOG/stretch
> Prices are estimates and change. Information, not financial advice.
