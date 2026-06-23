# Media Archive Check

Generated from `migration/media-inventory.csv` and the local media tar archive.

## Summary

| Metric | Count |
| --- | ---: |
| Inventory media rows | 41 |
| Archive files | 41 |
| Matched media rows | 41 |
| Missing media rows | 0 |
| Unattached inventory rows | 14 |
| Archive files not matched by inventory | 0 |

## Unattached or structural media

These rows have `parent_id` 0 or empty. They may be logos, cropped assets, loose uploads, or unused media.

| Post ID | Title | Expected path | Attachment URL |
| --- | --- | --- | --- |
| 8 | Zemelaar Logo | 2022/08/zemelaar-logo-white.png | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/zemelaar-logo-white.png |
| 12 | zemelaar-logo-dark | 2022/08/zemelaar-logo-dark.png | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/zemelaar-logo-dark.png |
| 22 | IMG_20220719_210910 | 2022/08/6fbcc-img_20220719_210910.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/6fbcc-img_20220719_210910.jpg |
| 23 | cropped-img_20220719_210910 | 2022/08/bd63f-cropped-img_20220719_210910.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/bd63f-cropped-img_20220719_210910.jpg |
| 13 | Zemelaar-logo-dark | 2022/08/zemelaar-logo-dark-1.png | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/zemelaar-logo-dark-1.png |
| 117 | IMG-20220724-WA0021 | 2022/08/img-20220724-wa0021.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/img-20220724-wa0021.jpg |
| 118 | IMG-20220804-WA0006 | 2022/08/img-20220804-wa0006.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/img-20220804-wa0006.jpg |
| 119 | IMG_20220726_205210 | 2022/08/img_20220726_205210.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/img_20220726_205210.jpg |
| 122 | FB_IMG_1661248876524 | 2022/08/fb_img_1661248876524.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2022/08/fb_img_1661248876524.jpg |
| 236 | 16c1fd02-d3be-45f5-8531-761b9b286b26-1 | 2025/06/16c1fd02-d3be-45f5-8531-761b9b286b26-1.png | https://zemelaarblog.wordpress.com/wp-content/uploads/2025/06/16c1fd02-d3be-45f5-8531-761b9b286b26-1.png |
| 247 | zemelaar-logo-new-1024 | 2025/06/zemelaar-logo-new-1024.png | https://zemelaarblog.wordpress.com/wp-content/uploads/2025/06/zemelaar-logo-new-1024.png |
| 254 | img_3578 | 2025/12/img_3578.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2025/12/img_3578.jpg |
| 256 | Screenshot | 2025/12/img_3288.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2025/12/img_3288.jpg |
| 258 | img_3695 | 2025/12/img_3695.jpg | https://zemelaarblog.wordpress.com/wp-content/uploads/2025/12/img_3695.jpg |

## Notes

This check matches expected WordPress upload paths against tar member paths. It does not extract files, compare checksums, or determine whether a media item is actually referenced inside post content.
