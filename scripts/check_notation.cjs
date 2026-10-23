/* Check the equations displayed by the website, including computed output. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.resolve(__dirname, '..');
const katex = require(path.join(root, 'dist/vendor/katex.min.js'));
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const context = {};
context.window = context;
vm.createContext(context);
vm.runInContext(read('dist/content.js'), context);
const equations = [];
function collect(value) {
  if (!value || typeof value !== 'object') return;
  for (const [key, item] of Object.entries(value)) {
    if (key === 'equations' && Array.isArray(item)) equations.push(...item.filter(x => typeof x === 'string'));
    else collect(item);
  }
}
collect(context.RAMAN_DOCS);
for (const file of ['dist/app.js', 'dist/optical-guide.js']) {
  for (const match of read(file).matchAll(/String\.raw`([^`]+)`/g)) equations.push(match[1]);
}
const catalog = JSON.parse(read('dist/data/catalog.json'));
for (const guide of Object.values(catalog.optical_guide)) {
  equations.push(...guide.states, guide.amplitude, guide.intensity);
}
const result = JSON.parse(read('dist/data/reference-example.json'));
for (const entry of result.equations) if (entry.kind === 'equation') {
  equations.push(entry.value);
  for (const symbol of entry.symbols || []) equations.push(symbol.latex);
}
for (const tex of equations) {
  katex.renderToString(tex, { displayMode: true, throwOnError: true, strict: 'ignore' });
}
if (catalog.version !== '4' || result.version !== '4') throw new Error('Unexpected release identity.');
if (!catalog.profiles.CUBIC_SIGMA.includes('σ⁺α')) throw new Error('Missing lowercase σ⁺α label.');
const code = JSON.parse(read('dist/data/cells.json')).cells;
if (!code[16].source.includes('4.1 Input θᵢ') || !code[16].source.includes('4.4 Detector βₛ')) throw new Error('Missing Greek input labels.');
if (result.latex.full.includes('beta_{prime}')) throw new Error('Unformatted β′ in the exported derivation.');
if (!result.latex.full.includes('beta^{\\prime}')) throw new Error('Missing β′ in the exported derivation.');
console.log(`Version 4 notation: ${equations.length} equations typeset; lowercase σ⁺α and Greek input labels passed.`);
