# ScoreIvy

An exam platform built with Next.js and React.

## Features

- Login page with username/password authentication
- Dashboard with "Take Test" button
- Interactive exam interface with multiple choice questions
- One question at a time with navigation

## Getting Started

First, install the dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

- `/app` - Next.js app directory
  - `/page.tsx` - Login page
  - `/dashboard` - Dashboard page (after login)
  - `/exam` - Exam/test page

## Usage

1. Navigate to the login page
2. Enter any username and password (validation accepts any non-empty values for demo)
3. Click "Login" to access the dashboard
4. Click "Take Test" to start the exam
5. Answer questions one at a time and click "Next" to proceed
6. Complete all 10 questions

