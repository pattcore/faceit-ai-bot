const path = require('path');
const fs = require('fs');

module.exports = {
  mode: 'production',
  entry: {
    background: './public/background.js',
    popup: './public/popup.js'
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    clean: false
  },
  resolve: {
    extensions: ['.js', '.json']
  },
  plugins: [
    {
      apply: (compiler) => {
        compiler.hooks.afterEmit.tap('AfterEmitPlugin', () => {
          // Создаем структуру для Chrome/Edge/Opera
          const chromeDir = path.resolve(__dirname, 'dist/chrome');
          if (!fs.existsSync(chromeDir)) {
            fs.mkdirSync(chromeDir, { recursive: true });
          }
          
          // Создаем структуру для Firefox
          const firefoxDir = path.resolve(__dirname, 'dist/firefox');
          if (!fs.existsSync(firefoxDir)) {
            fs.mkdirSync(firefoxDir, { recursive: true });
          }
          
          // Копируем собранные файлы
          const distDir = path.resolve(__dirname, 'dist');
          ['background.js', 'popup.js'].forEach(file => {
            const src = path.join(distDir, file);
            if (fs.existsSync(src)) {
              fs.copyFileSync(src, path.join(chromeDir, file));
              fs.copyFileSync(src, path.join(firefoxDir, file));
            }
          });
          
          // Создаем manifest.json для Chrome
          const chromeManifest = {
            manifest_version: 3,
            name: "Faceit Stats Bot",
            version: "0.2.1",
            description: "Анализ статистики и поиск тиммейтов в CS2",
            permissions: ["storage", "tabs"],
            host_permissions: ["https://www.faceit.com/*"],
            background: {
              service_worker: "background.js"
            },
            action: {
              default_popup: "popup.html",
              default_icon: {
                "16": "icon16.png",
                "48": "icon48.png",
                "128": "icon128.png"
              }
            },
            icons: {
              "16": "icon16.png",
              "48": "icon48.png",
              "128": "icon128.png"
            }
          };
          
          // Создаем manifest.json для Firefox
          const firefoxManifest = {
            manifest_version: 2,
            name: "Faceit Stats Bot",
            version: "0.2.1",
            description: "Анализ статистики и поиск тиммейтов в CS2",
            permissions: ["storage", "tabs", "https://www.faceit.com/*"],
            background: {
              scripts: ["background.js"]
            },
            browser_action: {
              default_popup: "popup.html",
              default_icon: {
                "16": "icon16.png",
                "48": "icon48.png",
                "128": "icon128.png"
              }
            },
            icons: {
              "16": "icon16.png",
              "48": "icon48.png",
              "128": "icon128.png"
            }
          };
          
          fs.writeFileSync(
            path.join(chromeDir, 'manifest.json'),
            JSON.stringify(chromeManifest, null, 2)
          );
          
          fs.writeFileSync(
            path.join(firefoxDir, 'manifest.json'),
            JSON.stringify(firefoxManifest, null, 2)
          );
          
          // Создаем простой popup.html
          const popupHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Faceit Stats Bot</title>
  <style>
    body {
      width: 300px;
      padding: 20px;
      font-family: Arial, sans-serif;
    }
    h1 {
      font-size: 18px;
      margin: 0 0 10px 0;
    }
    p {
      font-size: 14px;
      color: #666;
    }
    a {
      color: #667eea;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <h1>🎮 Faceit Stats Bot</h1>
  <p>Анализ статистики игроков на Faceit</p>
  <p><a href="https://pattmsc.online" target="_blank">Открыть веб-версию</a></p>
  <script src="popup.js"></script>
</body>
</html>`;
          
          fs.writeFileSync(path.join(chromeDir, 'popup.html'), popupHtml);
          fs.writeFileSync(path.join(firefoxDir, 'popup.html'), popupHtml);
          
          console.log('✅ Extension files created successfully!');
        });
      }
    }
  ]
};
