# MustangsMatter

This is a corrected submission for the HackSMU VI hackathon, which aimed to build a health and wellness platform for SMU students.

The original erroneous submission may be viewed live [here](https://wellness-web-app.onrender.com/).

## Deploying

This project was built with Python 3.12.7. The required dependencies for pip can be found in `requirements.txt`.

This project contains several secrets which must be provided as environment variables, specifically:
* `MONGODB_USER`: The username to authenticate into the MongoDB database
* `MONGODB_PASS`: The password to authenticate into the MongoDB database
* `PROPELAUTH_BASE`: The auth URL from PropelAuth frontend integration settings
* `PROPELAUTH_KEY`: The API key from PropelAuth backend integration settings
* `HUGGINGFACEHUB_API_TOKEN`: The API key to communicate with the HuggingFace LLM
