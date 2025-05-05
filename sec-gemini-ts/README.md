# Sec-Gemini TypeScript SDK

## Installation

## Basic usage

### Streaming API

### Synchronous API


## Running the demo

The `demo/demo.js` code demonstrates how to use the SDK. You can run it as follows:

**Linux/Mac**
```bash
SEC_GEMINI_API_KEY="YOUR_ACTUAL_API_KEY" npm run demo
```

**Windows CMD**
```bash
set SEC_GEMINI_API_KEY=your_key_here && npm run demo
```
**Windows PowerShell**
```bash
$env:SEC_GEMINI_API_KEY="your_key_here" && npm run demo
```

## Developement

### Install dependencies

```bash
npm install
```

### Using the local package

Build and then use npm link to use the package from source

```bash
npm run build
npm link
```

in your project/app

```bash
npm link sec-gemini
```

### Build for release

```bash
npm run build
```

### Runing tests

```bash
npm run test
```
