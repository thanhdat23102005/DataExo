# DataExodus — Speaker Script

Ten minutes, twelve slides. Each line break is a pause.
Speak to the audience; the slides only hold headlines.

## Slide 1 — Title  (0:00-0:15)

> Good morning. My name is Thanh Dat Phan.
> My project is called DataExodus.
> It answers one question.
> When you open a normal website - where does your data go?

*Delivery:* Ask the question, then stop. Look at the audience, not the screen.

## Slide 2 — A hash is not anonymous  (0:15-1:25)

> Here is the problem.
> A tracker does not send your email address.
> It sends a hash of it. This number here.
> And the company calls that anonymous.
> It is not anonymous.
> Here is why.
> The same email always makes the same hash. Always.
> So this number is still your name. You just cannot read it.
> Every website that receives this number sees the same person.
> The US Federal Trade Commission said this in 2024.
> My project does not only explain this.
> It proves it, on your own traffic.

*Delivery:* Say 'It is not anonymous' slowly, then pause two seconds. anonymous = uh-NON-uh-muss.

## Slide 3 — Why this matters in Australia  (1:25-2:25)

> Why does this matter here in Australia?
> We have a law. The Privacy Act. Principle 8.
> If a company sends your data overseas, it has duties.
> The ACCC studied this problem.
> They found that people cannot see who receives their data.
> So we have a law about it.
> But a normal person cannot check it.
> That gap is what I am building for.
> This is my own project. I have no client.

*Delivery:* Slow down on 'Principle 8'. Let the contrast land: there is a law, but no way to check it.

## Slide 4 — Two things you can install  (2:25-3:25)

> I am building two things. You can install both.
> First, a Chrome extension.
> It watches every request your browser makes.
> It names the company. It scores the risk.
> And it watches for your identifier leaving.
> Second, a Raspberry Pi application.
> It adds the country. It keeps the history.
> And it blocks trackers using DNS.
> DNS covers every device. Your phone. Your television.
> Those can never run an extension.
> One sentence to remember.
> The extension shows you the problem. The Pi does something about it.

*Delivery:* Point left for the extension, right for the Pi. Say the last two sentences slowly - this is the line they remember.

## Slide 5 — How the pieces fit  (3:25-4:40)

> This is the whole system on one slide.
> On the left is your home.
> The laptop runs the extension. The phone and the TV cannot.
> In the middle is the Raspberry Pi.
> At the top, the DNS sinkhole. It answers tracker questions with zero.
> Below that, the app. It receives the data and stores it.
> At the bottom, the dashboard.
> Now look at the orange bar.
> This is the privacy boundary.
> Your real email never crosses it. Full web addresses never cross it.
> Only hashes are compared. Only host names are sent.
> A web address contains your search words.
> This is a privacy tool. So I do not send it.

*Delivery:* Move your hand across the diagram, left to right. Then turn back and face the audience for the orange bar.

## Slide 6 — What it has to do  (4:40-5:40)

> Seven requirements on the left. What the system must do.
> Seven decisions on the right. How I do it.
> I will explain two of them.
> Number four. Hidden sharing, versus your own choice.
> You type your email into a search box. That is your choice. That is fine.
> The site sends your email hash to Facebook. That is not fine.
> At first my code treated both the same.
> Then everything looked like a leak.
> Now, normalisation.
> A tracker does not hash what you typed.
> It cleans the value first, then hashes it.
> I will show you why that matters.

*Delivery:* normalisation = nor-muh-lie-ZAY-shun. End with 'I will show you why' - it sets up slide ten.

## Slide 7 — Goals I can be held to  (5:40-6:25)

> Six goals. Each one has a number and a date.
> Together they cover every requirement.
> Look at goal four. Zero false positives.
> Not 'a few'. Zero.
> Because at the DNS layer, a mistake is not small.
> It removes a website for the whole house.
> And goal six says 'significant or not'.
> If I find nothing, I report nothing.
> This is a measurement. It is not an argument.

*Delivery:* Do not read all six goals. Name the number, then talk about goal four and goal six only.

## Slide 8 — Incremental layers, and why  (6:25-7:40)

> I build in layers. Each layer works on its own.
> Layer one, the extension. Layer two, the Pi.
> Layer three, blocking. Layer four, the study.
> Why not waterfall?
> My hardest questions are technical, and they come early.
> Waterfall would find them at the end. Too late to fix.
> Why not Scrum?
> Scrum meetings organise a team. I am one person.
> I kept the short steps. I dropped the meetings.
> And here is proof this was the right choice.
> My blocking code marked Wikipedia as a tracker. GitHub too.
> Why? A filter rule that blocks one page
> was read as blocking the whole website.
> At the DNS layer, that removes Wikipedia.
> For every device in the house.
> I found it because I tested that layer alone, before connecting it.

*Delivery:* This is your strongest story. Tell it fully. Pause before 'And here is proof'.

## Slide 9 — Tools chosen for a reason  (7:40-8:25)

> Now the tools. Quickly - the plan explains each one.
> I want to name two.
> DuckDB. My questions are like this:
> which company receives the most requests?
> That is what this database is built for. One file. No server.
> And dnslib, instead of a configuration file.
> I want my blocking logic to be code I can read and test.
> On standards: every list I use is public.
> So you can check any claim I make.
> That is on purpose.

*Delivery:* Keep this slide fast. It is supporting detail, not the main point.

## Slide 10 — Already built and tested  (8:25-9:25)

> This is the most important slide.
> None of this is a plan. I have run all of it.
> My MD5 code is tested against twelve known answers.
> That includes the sizes where hand-written MD5 usually breaks.
> Now the best example.
> You type your phone number with spaces.
> The tracker removes the spaces and adds the country code.
> Then it hashes that.
> My old code matched nothing. It reported no leak. Silently.
> My new code hashes every form.
> I have a test that proves the old one missed, and the new one matches.
> And zero false positives on blocking.
> That is goal four, already met.

*Delivery:* Pause after 'I have run all of it'. This slide answers 'is this student actually doing the work'.

## Slide 11 — What is left, and what could go wrong  (9:25-9:55)

> Week nine and ten: the full crawl of fifty sites.
> Week eleven: deployment and false positive testing.
> Week twelve and thirteen: dashboard and analysis.
> Week fourteen: the final presentation.
> Now one honest risk. The third one.
> Chrome has a setting called secure DNS.
> If someone turns it on, my Pi never sees their questions.
> I cannot stop that.
> But the extension still sees those requests.
> That is exactly why this project has two parts, not one.

*Delivery:* Do not rush because you are near the end. The risk slide shows you understand your own limits.

## Slide 12 — Close  (9:55-10:00)

> So. A hash is not anonymous.
> This project proves it on your own traffic. Then it blocks it.
> Thank you. I am happy to take questions.

*Delivery:* Stand still. Do not fill the silence. Wait for the first question.

### Likely questions

**Why not just use Pi-hole?**

Pi-hole blocks. It does not tell you who owns the destination, which country it is in, or whether your identifier went with it.

**Is this legal?**

Public pages only. My own traffic. My own identifier. No logins, no attacks. The same basis as published academic studies.

**Why only fifty sites?**

Because I check every classification by hand. Fifty is a number I can verify. Five thousand is a number I could only claim.

**What if you find nothing?**

Then I report that. It is a measurement, not an argument.

**How do you know your blocking is safe?**

I test it against a fixed list of twelve normal websites before deployment. Zero false positives is the pass condition, and I can roll the DNS setting back.
