13 Apr 2025:
[ ] Crawl image add agoda
[ ] Hotel widget webflow localization
[ ] Webflow api publishing
[ ] add faq content
[ ] hotel image name, caption and alt, add hotel name and keywords, also remove ";"
[ ] human UI for reviewing outline and edit
[ ] human UI for picking pictures and replce image by url
[ ] reduce image size to below 1mb before upload
[ ] Write facebook ad text (or use facebook ai)


=========

https://docs.perplexity.ai/guides/structured-outputs




Strapi API populate query builder
https://docs.strapi.io/cms/api/rest/interactive-query-builder
{
  populate: {
    blocks: { // asking to populate the blocks dynamic zone
      on: { // using a detailed population strategy to explicitly define what you want
        'theme-page-block.gallery': {
          populate: {
           'images': {
             populate: ['url']
           }
         }
        },
        'theme-page-block.hotel-widget': {
          populate: '*'
        }
      },
    },
  },
}