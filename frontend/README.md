This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, install dependencies:

```bash
npm install
```

Configure environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

Run the development server:

```bash
npm run dev
```

Open [http://localhost:5000](http://localhost:5000) with your browser to see the result.

## Configuration

Environment variables are defined in `.env.local` file (see `.env.example` for reference):

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:5001)
- `PORT` - Development server port (default: 5000)

Note: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Other variables are only available on the server side.
