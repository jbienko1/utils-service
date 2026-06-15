const path = require("path");

const root = __dirname;
const isWin = process.platform === "win32";
const python = path.join(root, ".venv", isWin ? "Scripts/python.exe" : "bin/python");
const logsDir = path.join(root, "logs", "pm2");

const viteBin = path.join("node_modules", "vite", "bin", "vite.js");

module.exports = {
  apps: [
    {
      name: "utils-api",
      cwd: root,
      script: python,
      args: "-m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      interpreter: "none",
      out_file: path.join(logsDir, "utils-api-out.log"),
      error_file: path.join(logsDir, "utils-api-error.log"),
    },
    {
      name: "utils-client-dev",
      cwd: path.join(root, "client"),
      script: viteBin,
      args: "",
      interpreter: "node",
      out_file: path.join(logsDir, "utils-client-dev-out.log"),
      error_file: path.join(logsDir, "utils-client-dev-error.log"),
    },
    {
      name: "utils-client-preview",
      cwd: path.join(root, "client"),
      script: viteBin,
      args: "preview",
      interpreter: "node",
      out_file: path.join(logsDir, "utils-client-preview-out.log"),
      error_file: path.join(logsDir, "utils-client-preview-error.log"),
    },
  ],
};
