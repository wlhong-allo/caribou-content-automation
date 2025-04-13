
1. Click to open thumbnail gallery
document.querySelector("#Overview > div > div > div.uitk-layout-position.uitk-layout-position-zindex-layer2.uitk-layout-position-bottom-three.uitk-layout-position-right-three.uitk-layout-position-absolute > div > button")


2. Click to open the media gallery
document.querySelector("#app-layer-thumbnail-gallery > section > div.uitk-sheet-content > div > div.uitk-spacing.uitk-spacing-padding-blockend-three.uitk-spacing-padding-small-inline-three.uitk-spacing-padding-medium-inline-three > ul > div > div:nth-child(1) > div:nth-child(1) > div > li > button")


3. find app-layer-media-gallery
document.querySelector("#app-layer-media-gallery > section > div.uitk-sheet-content > div > div.uitk-carousel.no-peek.no-touch.full-image-gallery-type.has-persistent-nav.uitk-spacing.uitk-spacing-padding-block-four.uitk-spacing-padding-inline-three.uitk-layout-flex-item.xl > div.uitk-carousel-container.full-image-gallery-type.use-container-sizing")


4. Loop through the child to find below <img>, get src and alt attributes
document.querySelector("#app-layer-media-gallery > section > div.uitk-sheet-content > div > div.uitk-carousel.no-peek.no-touch.full-image-gallery-type.has-persistent-nav.uitk-spacing.uitk-spacing-padding-block-four.uitk-spacing-padding-inline-three.uitk-layout-flex-item.xl > div.uitk-carousel-container.full-image-gallery-type.use-container-sizing > div:nth-child(1) > figure > div > img")