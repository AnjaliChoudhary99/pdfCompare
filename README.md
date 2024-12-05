# pdfCompare
1. install the dependencies needed
2. run on local machine use the command: uvicorn fast2:app --reload

2 routes

a. GET "/" : (home route) provides UI to submit 2 pdfs to compare

b. POST "/upload-pdf/" : is hit internally throigh the HTML form on home page, processes the PDFs provided and generates a comparison PDF.

For swagger : use this route -  "/docs"

You can use the sample PDFs to test.
