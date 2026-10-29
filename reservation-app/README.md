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
If the backend isn't running, the API modules fall back to seed data kept in `localStorage`,
so the UI still works for demos.

Other scripts: `npm run lint`, `npm run build` (output in `dist/`, which `desktop_app.py` serves).

## Test accounts

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
                       (each has a localStorage fallback and the seed data)
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
