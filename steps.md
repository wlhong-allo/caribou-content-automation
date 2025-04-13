Input: 
Origin Country/Market (O) (e.g.: Australia, Hong Kong)
Destination Cities/District/Metro station (D) (e.g.: Osaka, Tennoji, Denparsar, Ubud)
Niche segments
Niche needs 
Language (default to English if not specified)

#Part 1: SEO research:
[ ] Get keyword inspiration from Google destination insight (specified Origin (O) and Destination (D), use the same 90 days periods from last year)
https://destinationinsights.withgoogle.com/intl/en_ALL/
[ ] Generate an aggregated list of destination Cities from "City and regional demand" and "Growth of demand"
https://app.ahrefs.com/keywords-explorer (require login)
[ ] put the list to Ahrefs keyword explorer, choose the correct Origin country, get a list of high Search Volume (SV) keywords
https://docs.google.com/spreadsheets/d/1u52aAE6WePEKL9OW-do8ZlVPQV9irr1iULGChHI04RY/edit?gid=0#gid=0
[ ] for each keyword on the list, find total 9-12 hotels, by going to Agoda, Trip.com, Booking.com and each find the top 3-4 hotels, input the keyword, pick a day 45 from now, go through the list from top, look for nice photo, high review
https://docs.google.com/spreadsheets/d/1u52aAE6WePEKL9OW-do8ZlVPQV9irr1iULGChHI04RY/edit?gid=1369015969#gid=1369015969 (example of ubud)

Content Generation:

[ ] Keyword cluster, Q&A and titles
https://www.perplexity.ai/search/i-am-writing-an-articles-of-to-cTyZVtAuQ9Ki9aboS8UaNQ

[ ] Outline Generation: Titles, meta, keyword clusters, paragraphs outline 
https://www.perplexity.ai/search/you-are-a-popular-blogger-from-KqGolmTXRumm3oQCvdU_zg

[ ] Content Generation: Final title, complete article, images with alt description


[ ] OG thumbnail image and text generation, replace on Canva:
Prompt: 
I am creating the thumbnail picture for the above article, referring to the graphic composition of the attached image, 
1) please help to find 3 image options for me to choose from replacing the key image
2) And write the corresponding title and description text on the image
https://www.canva.com/design/DAGB0VaK45o/ZzMT46osfRhkb-RUXdnPEA/edit

[ ] Affiliate links generation
Use Computer use to find all url, and pass to retool (4-url-extraction-prompt)
API
Check retool repo: 
https://cariboutraveldev.retool.com/apps/8daa512a-667d-11ee-8a23-53077ca4622a/Affiliation%20Link%20Conversion
Login by reservation@

[ ] Hotel Image preparation
Using expedia link
Using crawl4ai, check crawl/main.py

[ ] Content adaptation to Strapi and Webflow
API

Publishing:

[ ] Facebook ad segment creation
[ ] Facebook ad creation