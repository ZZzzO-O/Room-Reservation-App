# Classroom Reservation Application

## Project Overview

The Classroom Reservation Application is a modern React-based web solution developed for managing and booking academic spaces, lecture halls, and study pods efficiently. Built as part of University coursework and engineered under strict "Team Vibranium" coding standards, this application emphasizes modular frontend architecture, clean code readability, JSDoc documentation, and a seamless user experience complete with a responsive dark mode interface.

## Architecture and Project Structure

The project follows a strict separation of concerns to maintain scalability and modularity. All application logic is neatly organized within the source directory using a predictable directory layout.

The API layer resides in the `src/api` directory, housing service modules like `roomApi.js` which handle backend communication and mock data retrieval.

The user interface elements and reusable UI blocks, such as the navigation bar and individual room display cards, are located within the `src/components` directory under files like `NavBar.jsx` and `RoomCard.jsx`.

The primary views and dashboard containers are housed in the `src/pages` directory, featuring files like `HomePage.jsx` which manage state, coordinate components, and apply filtering logic.

## Core Features

The application features a fully interactive room browsing dashboard that retrieves available facilities dynamically through asynchronous service functions. Users can toggle between a clean light mode and a comfortable dark mode interface instantly, utilizing custom CSS styling classes configured globally. The application also implements strict JSDoc documentation across all components and helper functions to ensure high code maintainability and robust type hinting.

## Prerequisites

Before you begin, ensure you have Node.js and npm installed on your local machine. You can verify your installation by running `node -v` and `npm -v` in your terminal.

## Installation and Setup

To set up the project locally on your machine, follow these steps sequentially.

First, clone the repository or open your existing project folder in your terminal and navigate into the application directory:

```bash
cd reservation-app
```

Next, install all required dependencies:

```bash
npm install
```

Finally, start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173` by default.

## Built With

- [React](https://react.dev/) — UI library
- [Vite](https://vitejs.dev/) — Build tool and dev server
- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) — React Fast Refresh via Babel