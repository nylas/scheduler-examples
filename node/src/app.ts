import express from "express";
import flash from "express-flash";
import session from "express-session";
import bodyParser from "body-parser";
import compression from "compression"; // compresses requests
import consolidate from "consolidate";
import lusca from "lusca";
import path from "path";
import Nylas from "nylas";

// Controllers (route handlers)
import router from "./controllers/base";

const NylasClientID = process.env["NYLAS_OAUTH_CLIENT_ID"];
const NylasClientSecret = process.env["NYLAS_OAUTH_CLIENT_SECRET"];

if (!NylasClientID || !NylasClientSecret) {
  console.warn(`
    To run this example, pass the NYLAS_OAUTH_CLIENT_ID and NYLAS_OAUTH_CLIENT_SECRET
    environment variables when launching the service. eg:\n
    REDIRECT_URI=https://ad172180.ngrok.io/login_callback NYLAS_OAUTH_CLIENT_ID=XXX NYLAS_OAUTH_CLIENT_SECRET=XXX npm start
  `);
  process.exit(1);
}

// Configure Nylas
Nylas.config({
  appId: NylasClientID,
  appSecret: NylasClientSecret
});

// Create Express server
const app = express();

// assign the mustache enging to .mustache files
app.engine("mustache", consolidate.mustache);

// Express configuration
app.set("port", process.env["PORT"] || 5000);
app.set("views", path.join(__dirname, "../views"));
app.set("view engine", "mustache");
app.use(compression());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(
  session({
    resave: true,
    saveUninitialized: true,
    secret: process.env["SECRET_KEY"] || "test-secret",
    cookie: { maxAge: 60000 }
  })
);
app.use(flash());
app.use(lusca.xframe("SAMEORIGIN"));
app.use(lusca.xssProtection(true));

app.use(
  express.static(path.join(__dirname, "public"), { maxAge: 31557600000 })
);

app.use(router);

export default app;
