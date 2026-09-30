"""
visualizer.py - Interactive `range()` Visualizer Component for Teammate 2
Embedded directly into the Lesson page via streamlit.components.v1.html
Allows students to interactively test start, stop, step and watch loop execution step-by-step.
"""

def render_range_visualizer(start=0, stop=5, step=1):
    """
    Returns self-contained HTML/CSS/JS for an interactive, animated range() simulator.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <style>
        * {{
          box-sizing: border-box;
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        body {{
          background: #0f172a;
          color: #e2e8f0;
          padding: 16px;
          border-radius: 14px;
        }}
        .vis-container {{
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }}
        .vis-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }}
        .vis-title {{
          font-size: 15px;
          font-weight: 700;
          color: #38bdf8;
          display: flex;
          align-items: center;
          gap: 8px;
        }}
        .vis-controls {{
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          margin-bottom: 18px;
          align-items: center;
          background: #0f172a;
          padding: 12px;
          border-radius: 10px;
        }}
        .control-group {{
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
        }}
        .control-group label {{
          color: #94a3b8;
          font-weight: 600;
        }}
        .control-group input {{
          background: #1e293b;
          border: 1px solid #475569;
          color: #f8fafc;
          border-radius: 6px;
          width: 54px;
          padding: 5px 8px;
          font-weight: bold;
          text-align: center;
        }}
        .btn-action {{
          background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
          border: none;
          color: white;
          padding: 7px 16px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 12px;
          cursor: pointer;
          transition: 0.2s;
        }}
        .btn-action:hover {{
          filter: brightness(1.15);
          transform: translateY(-1px);
        }}
        .code-preview {{
          font-family: 'Courier New', monospace;
          background: #090d16;
          border: 1px solid #1e293b;
          border-radius: 8px;
          padding: 10px 14px;
          color: #38bdf8;
          font-size: 14px;
          margin-bottom: 18px;
        }}
        .code-preview span.keyword {{ color: #f472b6; }}
        .code-preview span.func {{ color: #38bdf8; }}
        .code-preview span.num {{ color: #facc15; }}
        .strip {{
          display: flex;
          gap: 10px;
          overflow-x: auto;
          padding: 12px 6px;
          margin-bottom: 16px;
        }}
        .node {{
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-width: 52px;
          height: 60px;
          border-radius: 10px;
          background: #334155;
          border: 2px solid #475569;
          font-size: 16px;
          font-weight: 700;
          color: #cbd5e1;
          transition: all 0.3s ease;
          position: relative;
        }}
        .node.included {{
          background: rgba(14, 165, 233, 0.2);
          border-color: #0284c7;
          color: #38bdf8;
        }}
        .node.current-step {{
          background: #0284c7;
          color: white;
          box-shadow: 0 0 16px #38bdf8;
          transform: scale(1.1);
        }}
        .node.excluded {{
          background: rgba(239, 68, 68, 0.1);
          border-color: #ef4444;
          color: #f87171;
          opacity: 0.7;
          border-style: dashed;
        }}
        .node-tag {{
          font-size: 9px;
          text-transform: uppercase;
          margin-top: 2px;
          font-weight: 800;
          letter-spacing: 0.5px;
        }}
        .output-box {{
          background: #090d16;
          border: 1px solid #1e293b;
          border-radius: 8px;
          padding: 10px 14px;
          font-size: 12px;
          color: #94a3b8;
          min-height: 48px;
          display: flex;
          align-items: center;
          gap: 8px;
        }}
        .pill {{
          display: inline-block;
          padding: 3px 8px;
          border-radius: 4px;
          background: #10b981;
          color: #022c22;
          font-weight: bold;
          font-size: 11px;
        }}
      </style>
    </head>
    <body>
      <div class="vis-container">
        <div class="vis-header">
          <div class="vis-title">
            <span>⚙️</span> Interactive range(start, stop, step) Visualizer
          </div>
        </div>

        <div class="vis-controls">
          <div class="control-group">
            <label>Start:</label>
            <input type="number" id="in-start" value="{start}">
          </div>
          <div class="control-group">
            <label>Stop:</label>
            <input type="number" id="in-stop" value="{stop}">
          </div>
          <div class="control-group">
            <label>Step:</label>
            <input type="number" id="in-step" value="{step}">
          </div>
          <button class="btn-action" onclick="renderVisualizer()">Update Strip</button>
          <button class="btn-action" style="background: linear-gradient(135deg, #10b981, #059669);" onclick="animateLoop()">▶ Run Loop</button>
        </div>

        <div class="code-preview" id="code-str">
          <span class="keyword">for</span> i <span class="keyword">in</span> <span class="func">range</span>(<span class="num">{start}</span>, <span class="num">{stop}</span>, <span class="num">{step}</span>):
        </div>

        <div class="strip" id="strip"></div>

        <div class="output-box">
          <span style="color: #38bdf8; font-weight: 600;">Console Output:</span>
          <span id="console-stream">Click 'Run Loop' to simulate iterations...</span>
        </div>
      </div>

      <script>
        let currentStepIndex = -1;
        let animationTimer = null;

        function getValues() {{
          const start = parseInt(document.getElementById('in-start').value) || 0;
          const stop = parseInt(document.getElementById('in-stop').value) || 0;
          const step = parseInt(document.getElementById('in-step').value) || 1;
          return {{ start, stop, step }};
        }}

        function renderVisualizer() {{
          if (animationTimer) clearInterval(animationTimer);
          const {{ start, stop, step }} = getValues();
          const strip = document.getElementById('strip');
          const codeStr = document.getElementById('code-str');
          const consoleStream = document.getElementById('console-stream');
          
          codeStr.innerHTML = `<span class="keyword">for</span> i <span class="keyword">in</span> <span class="func">range</span>(<span class="num">${{start}}</span>, <span class="num">${{stop}}</span>, <span class="num">${{step}}</span>):`;
          strip.innerHTML = '';
          consoleStream.innerText = 'Ready to iterate.';

          const values = [];
          if (step > 0) {{
            for (let i = start; i < stop; i += step) values.push(i);
          }} else if (step < 0) {{
            for (let i = start; i > stop; i += step) values.push(i);
          }}

          // Build preview elements strictly up to stop (inclusive) to visually highlight exclusion, without extra boxes after stop!
          const maxDisplay = Math.max(stop, start);
          const minDisplay = Math.min(start, stop);

          for (let n = minDisplay; n <= maxDisplay; n++) {{
            const isIncluded = values.includes(n);
            const isStop = (n === stop);
            
            const node = document.createElement('div');
            node.className = 'node ' + (isIncluded ? 'included' : (isStop ? 'excluded' : ''));
            node.id = 'node-' + n;
            
            let tag = '';
            if (n === start && isIncluded) tag = 'START';
            else if (isStop) tag = 'STOP (EXCL)';
            else if (isIncluded) tag = 'STEP';

            node.innerHTML = `<div>${{n}}</div><div class="node-tag">${{tag}}</div>`;
            strip.appendChild(node);
          }}
        }}

        function animateLoop() {{
          const {{ start, stop, step }} = getValues();
          const values = [];
          if (step > 0) {{
            for (let i = start; i < stop; i += step) values.push(i);
          }} else if (step < 0) {{
            for (let i = start; i > stop; i += step) values.push(i);
          }}

          if (values.length === 0) {{
            document.getElementById('console-stream').innerText = 'Loop generated 0 iterations (Condition unmet).';
            return;
          }}

          let idx = 0;
          document.getElementById('console-stream').innerText = '';
          if (animationTimer) clearInterval(animationTimer);

          animationTimer = setInterval(() => {{
            // Clear previous highlight
            document.querySelectorAll('.node').forEach(el => el.classList.remove('current-step'));
            
            if (idx < values.length) {{
              const val = values[idx];
              const targetNode = document.getElementById('node-' + val);
              if (targetNode) targetNode.classList.add('current-step');
              
              const currentConsole = document.getElementById('console-stream');
              currentConsole.innerHTML += `<span class="pill">${{val}}</span> `;
              idx++;
            }} else {{
              clearInterval(animationTimer);
              const stopNode = document.getElementById('node-' + stop);
              if (stopNode) stopNode.classList.add('excluded');
              document.getElementById('console-stream').innerHTML += ` <span style="color:#ef4444; font-weight:bold;">[Stop ${{stop}} reached -> Loop Exits]</span>`;
            }}
          }}, 600);
        }}

        // Initial render
        renderVisualizer();
      </script>
    </body>
    </html>
    """
    return html_code
