import express, { Request, Response } from "express";
import request from "request-promise";
import Nylas from "nylas";

const redirectURI =
  "https://nylas-customer-example-nodejs.herokuapp.com/login_callback";

const router = express.Router();

router.get("/", async (req: Request, res: Response) => {
  const accessToken = req.session["access_token"];
  if (!accessToken) {
    res.render("base", {
      login_href: Nylas.urlForAuthentication({
        redirectURI,
        scopes: ["calendar"]
      }),
      insecure_override: req.protocol !== "https",
      partials: { authorization_partial: "partials/before_authorized" }
    });
    return;
  }

  const nylas = Nylas.with(accessToken);
  const account = await nylas.account.get();

  // If the user has already connected to Nylas via OAuth,
  // `nylas.authorized` will be true. Otherwise, it will be false.
  const pages = await request.get({
    uri: "https://schedule.api.nylas.com/manage/pages",
    headers: { Authorization: `Bearer ${accessToken}` },
    json: true
  });

  res.render("base", {
    pages,
    account,
    accessToken,
    partials: { authorization_partial: "partials/after_authorized" }
  });
});

router.post("/", async (req: Request, res: Response) => {
  const accessToken = req.session["access_token"];
  if (!accessToken) {
    res.redirect("/");
    return;
  }

  const newPage = await request.post({
    uri: "https://schedule.api.nylas.com/manage/pages",
    json: true,
    body: {
      name: req.body["name"],
      slug: req.body["slug"],
      api_tokens: [accessToken],
      config: {
        // You can provide as few or as many page configuration options as you like.
        // Check out the Scheduling Page documentation for a full list of settings.
        event: {
          title: req.body["event_title"]
        }
      }
    }
  });

  res.redirect("/");
});

router.get("/login_callback", async (req: Request, res: Response) => {
  if (req.query.error) {
    res.status(400).send(`Login error: ${req.query["error"]}`);
    return;
  }

  const token = await Nylas.exchangeCodeForToken(req.query.code);

  // save the token to the current session, save it to the user model, etc.
  req.session["access_token"] = token;

  res.redirect("/");
});

export default router;
