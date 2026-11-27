/* Run the notebook's scientific functions in an isolated Python worker. */
let pythonReady;
let currentRequest = null;
self.pythonProgress = message => self.postMessage({kind: 'progress', id: currentRequest, message});

async function initializePython() {
  const base = new URL('./vendor/pyodide/', self.location.href).href;
  self.pythonProgress('Starting Python. The first run may take a moment…');
  importScripts(base + 'pyodide.js');
  const paths = ['./raman_engine.py', './web_bridge.py', './web-fast.py?v=b984edf08127'];
  const [python, sources] = await Promise.all([
    (async () => {
      const py = await loadPyodide({indexURL: base, stdout: () => {}, stderr: text => {
        if (!text.startsWith('findfont:')) self.postMessage({kind: 'log', message: text});
      }});
      self.pythonProgress('Loading NumPy, SymPy and Matplotlib…');
      await py.loadPackage(['numpy', 'sympy', 'matplotlib']);
      return py;
    })(),
    Promise.all(paths.map(async path => {
      const response = await fetch(new URL(path, self.location.href));
      if (!response.ok) throw new Error(`Could not load ${path}: HTTP ${response.status}`);
      return response.text();
    })),
  ]);
  for (const source of sources) await python.runPythonAsync(source);
  self.pythonProgress('Python ready.');
  return python;
}

self.onmessage = async event => {
  const {id, type, payload = {}} = event.data;
  currentRequest = id;
  try {
    if (!pythonReady) pythonReady = initializePython();
    const py = await pythonReady;
    let result, binary = false;
    if (type === 'init') result = {ready: true, version: '5'};
    else {
      py.globals.set('web_input_json', JSON.stringify(payload));
      const expressions = {
        calculate: 'web_calculate(web_input_json)',
        calculateQuick: 'web_quick_calculate(web_input_json)',
        details: 'web_calculation_details()',
        preflight: 'web_preflight(web_input_json)',
        export: 'web_export()',
        figure: 'web_download_figure(json.loads(web_input_json)["index"], json.loads(web_input_json)["extension"])',
        validate: 'web_validate()',
        addComparison: 'web_add_comparison()',
        clearComparisons: 'web_clear_comparisons()',
        compare: 'web_compare(json.loads(web_input_json)["channel"], json.loads(web_input_json)["normalized"])',
        benchmark: 'web_benchmark(json.loads(web_input_json)["magnitude"], json.loads(web_input_json)["points"])',
        exportBenchmark: 'web_export_benchmark()',
      };
      if (!(type in expressions)) throw new Error('Unknown calculator operation.');
      result = await py.runPythonAsync(expressions[type]);
      binary = ['export', 'figure', 'exportBenchmark'].includes(type);
      if (binary) {
        const converted = result.toJs();
        result.destroy();
        const buffer = new Uint8Array(converted).buffer;
        self.postMessage({kind: 'result', id, binary: true, buffer}, [buffer]);
        return;
      }
      result = JSON.parse(result);
    }
    self.postMessage({kind: 'result', id, result});
  } catch (error) {
    if (type === 'init') pythonReady = null;
    self.postMessage({kind: 'error', id, message: String(error.message || error)});
  } finally { currentRequest = null; }
};
