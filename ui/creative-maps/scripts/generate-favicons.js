import { favicons } from 'favicons';
import fs from 'node:fs';
import path from 'node:path';

const SOURCE = './public/favicon.svg'; // Save the SVG here
const OUTPUT = './public/';

const configuration = {
  //  path: "/icons/", // Path for overriding default icons path
  //  appName: "Filonov",
  //  appShortName: "Filonov",
  //  appDescription: "Filonov Ad Assets Analysis",
  //  background: "#ffffff",
  //  theme_color: "#2a4858",
  //  appleStatusBarStyle: "default",
  //  display: "standalone",
  //  orientation: "portrait",
  //  scope: "/",
  //  start_url: "/",
  //  version: "1.0",
  logging: false,
  icons: {
    favicons: true,
    android: false,
    appleIcon: true,
    appleStartup: false,
    windows: false,
    yandex: false,
  },
};

async function run() {
  const iconsPath = path.join(OUTPUT, 'icons');
  if (!fs.existsSync(iconsPath)) {
    fs.mkdirSync(iconsPath, { recursive: true });
  }

  // Generate favicons
  const response = await favicons(SOURCE, configuration);

  // Write the files
  await Promise.all(
    response.images.map(async (image) => {
      let outputPath;
      if (image.name === 'favicon.ico') {
        outputPath = path.join(OUTPUT, image.name);
      } else {
        outputPath = path.join(OUTPUT, 'icons', image.name);
      }
      await fs.promises.writeFile(outputPath, image.contents);
      console.log('created ' + image.name);
    }),
  );

  console.log('Favicon generation completed!');
}

run().catch(console.error);

/*
(async () => {
  try {
    const iconsPath = path.join(OUTPUT, 'icons');
    if (!fs.existsSync(iconsPath)) {
      fs.mkdirSync(iconsPath, { recursive: true });
    }

    // Generate favicons
    const response = await favicons(SOURCE, configuration);

    // Write the files
    await Promise.all(
      response.images.map(async (image) => {
        let outputPath;
        if (image.name === 'favicon.ico') {
          outputPath = path.join(OUTPUT, image.name);
        } else {
          outputPath = path.join(OUTPUT, 'icons', image.name);
        }
        await fs.promises.writeFile(outputPath, image.contents);
        console.log('created ' + image.name);
      }),
    );

    //await Promise.all(response.files.map(async (file) => {
    //  await fs.promises.writeFile(path.join(OUTPUT, file.name), file.contents);
    //  console.log('created ' + file.name);
    //}));

    console.log('Favicon generation completed!');
  } catch (error) {
    console.error('An error occurred:', error);
  }
})();
*/