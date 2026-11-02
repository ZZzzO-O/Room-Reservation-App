# reservation-app

React front end for the Classroom Reservation Application (SEN-201, Team Vibranium).
Built with Vite, React 19 and Tailwind CSS v4.

## Running it

Start the API gateway first (from the repo root):

```bash
python ApiGateway/api_gateway.py      # serves the API on http://127.0.0.1:5000
```

Then start the dev server:

```bash
cd reservation-app
npm install
npm run dev                           # http://localhost:5173
```

`vite.config.js` proxies `/api/*` to port 5000, so the browser only talks to the dev server.
In development, if the backend isn't running, the API modules fall back to seed
data kept in `localStorage`, so the UI still works for demos. Production builds
do not use local fallback data.

Other scripts: `npm run lint`, `npm run build` (output in `dist/`, which `desktop_app.py` serves).

## Open or install the hosted web app

Open the Render HTTPS URL in a supported browser; no client-side Python, Node.js,
or Docker installation is needed. On desktop Chrome/Edge, choose **Install app**
or **Create shortcut** in the browser menu. On Android Chrome choose **Install
app** or **Add to Home screen**. On iPhone/iPad, use Safari's **Share → Add to
Home Screen** option.

The web manifest and icons provide the install experience. A service worker
caches the application shell and static assets, but the backend API requires an
internet connection. It does not provide offline reservation synchronization.

## Development test accounts

| Email               | Password    | Role      |
| ------------------- | ----------- | --------- |
| `staff1@cmkl.ac.th` | `Test@1234` | Staff     |
| `prof1@cmkl.ac.th`  | `Test@1234` | Professor |

Staff can add, edit, close and delete rooms. Both roles can book.

## Layout

```
src/
  App.jsx              view switching, current user, rooms + reservations state
  api/                 fetch wrappers for /api/auth, /api/rooms, /api/reservations
                       (development-only localStorage fallback and seed data)
  components/
    ModalShell.jsx     shared dialog frame: overlay, title, Escape to close
    NavBar.jsx, RoomCard.jsx, *Modal.jsx
  pages/               BrowsePage (rooms), MyReservationsPage, SchedulePage
  utils/styles.js      shared class strings for inputs and buttons
  index.css            Tailwind entry + brand colour and font tokens
```

## Styling

All accent colours use the `brand-*` scale defined in `src/index.css`. Change it there to
re-theme the app. See `DESIGN.md` in the repo root for the rules we follow.
