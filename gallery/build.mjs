import { build } from './lib/build.mjs';

const n = await build('entries', 'dist');
console.log(`built ${n} entries into dist/`);
