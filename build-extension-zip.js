const fs = require('fs');
const path = require('path');
const yazl = require('yazl');

const EXTENSION_DIR = path.join(__dirname, 'extension');
const OUTPUT_DIR = path.join(__dirname, 'public', 'assets', 'prod');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'faceit-ai-bot-extension.zip');

function addDirectoryToZip(zip, dirPath, baseInZip = '') {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    const relPath = baseInZip ? `${baseInZip}/${entry.name}` : entry.name;

    if (entry.isDirectory()) {
      addDirectoryToZip(zip, fullPath, relPath);
    } else if (entry.isFile()) {
      zip.addFile(fullPath, relPath);
    }
  }
}

async function main() {
  try {
    if (!fs.existsSync(EXTENSION_DIR)) {
      console.error(`Extension directory not found: ${EXTENSION_DIR}`);
      process.exit(1);
    }

    fs.mkdirSync(OUTPUT_DIR, { recursive: true });

    const zip = new yazl.ZipFile();
    addDirectoryToZip(zip, EXTENSION_DIR);

    await new Promise((resolve, reject) => {
      const outStream = fs.createWriteStream(OUTPUT_FILE);
      outStream.on('close', resolve);
      outStream.on('error', reject);

      zip.outputStream.pipe(outStream);
      zip.end();
    });

    console.log(`✅ Extension archived to ${OUTPUT_FILE}`);
  } catch (e) {
    console.error('Failed to build extension ZIP', e);
    process.exit(1);
  }
}

main();
