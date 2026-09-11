Use mongodb to store user and AI conversation since it provides flexibility relative to postgres

Use postgres to store permissions, scope and related information on the user

We are also going to have to create an auth for the user to make requests, and send it to the frontend to use as a key to perform requests, that way the api must depend on a key to decode and use to make requests.


Auth server for scopes will be its own server, by which we will pull data from onto this server



<!--[C:\Users\HP\AppData\Roaming\gcloud\application_default_credentials.json]-->
