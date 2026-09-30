"""
animations.py - Creative Interactive Animations for LearnMate AI
Provides render_animation(animation_name) for embedding interactive micro-simulators
into Streamlit lesson sections.
"""
import streamlit as st
import streamlit.components.v1 as components
from typing import Union, Optional, Any

def render_range_visualizer_html() -> str:
    """Returns self-contained HTML/CSS/JS for an interactive range() visualizer."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: #0b0f19; color: #e2e8f0; padding: 12px; }
        .vis-card {
          background: #111827;
          border: 1px solid #1f2937;
          border-radius: 12px;
          padding: 18px;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .title { font-size: 14.5px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
        .badge { background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
        
        .controls {
          display: flex;
          gap: 12px;
          align-items: center;
          background: #1e293b;
          padding: 10px 14px;
          border-radius: 8px;
          margin-bottom: 16px;
          flex-wrap: wrap;
        }
        .ctrl-group { display: flex; align-items: center; gap: 6px; font-size: 13px; }
        .ctrl-group label { color: #94a3b8; font-weight: 600; }
        .ctrl-group input {
          background: #0f172a;
          border: 1px solid #334155;
          color: #f8fafc;
          border-radius: 6px;
          width: 50px;
          padding: 4px 6px;
          text-align: center;
          font-weight: bold;
          font-size: 13px;
        }
        .btn-run {
          background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
          border: none;
          color: white;
          padding: 6px 14px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 12px;
          cursor: pointer;
          transition: transform 0.1s, filter 0.2s;
        }
        .btn-run:hover { filter: brightness(1.15); transform: translateY(-1px); }
        
        .code-strip {
          font-family: 'JetBrains Mono', 'Courier New', monospace;
          background: #030712;
          border: 1px solid #1f2937;
          border-radius: 6px;
          padding: 8px 12px;
          font-size: 13px;
          color: #a5b4fc;
          margin-bottom: 16px;
        }
        .code-strip .fn { color: #f43f5e; font-weight: bold; }
        .code-strip .val { color: #fbbf24; font-weight: bold; }
        
        .track-container {
          background: #090d16;
          border: 1px dashed #334155;
          border-radius: 10px;
          padding: 16px 12px;
          overflow-x: auto;
          margin-bottom: 14px;
        }
        .track-label { font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.5px; }
        .track {
          display: flex;
          gap: 8px;
          align-items: center;
          min-height: 60px;
        }
        .cell {
          width: 44px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 14px;
          border: 1px solid #334155;
          background: #1e293b;
          color: #94a3b8;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
        }
        .cell .idx { font-size: 9px; color: #64748b; margin-top: 2px; }
        .cell.yielded {
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.3) 100%);
          border-color: #10b981;
          color: #34d399;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        }
        .cell.active {
          background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%);
          border-color: #38bdf8;
          color: #ffffff;
          transform: scale(1.08) translateY(-3px);
          box-shadow: 0 6px 16px rgba(56, 189, 248, 0.4);
        }
        .cell.excluded {
          background: rgba(239, 68, 68, 0.15);
          border: 2px dashed #ef4444;
          color: #f87171;
        }
        .cell.excluded::after {
          content: "STOP";
          position: absolute;
          top: -10px;
          font-size: 8px;
          background: #ef4444;
          color: white;
          padding: 1px 4px;
          border-radius: 4px;
          font-weight: 800;
        }
        
        .output-box {
          background: #030712;
          border-radius: 8px;
          padding: 10px 14px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 12.5px;
          color: #cbd5e1;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .output-box b { color: #34d399; }
        .rule-note {
          margin-top: 10px;
          font-size: 12px;
          color: #f59e0b;
          display: flex;
          align-items: center;
          gap: 6px;
        }
      </style>
    </head>
    <body>
      <div class="vis-card">
        <div class="header">
          <div class="title">
            <span>⚙️</span> Interactive range(start, stop, step) Simulator
          </div>
          <span class="badge">Live Animation</span>
        </div>
        
        <div class="controls">
          <div class="ctrl-group">
            <label>start:</label>
            <input type="number" id="in-start" value="1" min="0" max="15">
          </div>
          <div class="ctrl-group">
            <label>stop:</label>
            <input type="number" id="in-stop" value="6" min="1" max="15">
          </div>
          <div class="ctrl-group">
            <label>step:</label>
            <input type="number" id="in-step" value="2" min="1" max="5">
          </div>
          <button class="btn-run" onclick="runSimulation()">▶ Run Loop</button>
          <button class="btn-run" style="background:#334155;" onclick="stepOnce()">⏭ Step</button>
        </div>
        
        <div class="code-strip" id="code-preview">
          for i in <span class="fn">range</span>(<span class="val" id="disp-start">1</span>, <span class="val" id="disp-stop">6</span>, <span class="val" id="disp-step">2</span>):
        </div>
        
        <div class="track-container">
          <div class="track-label">Sequence Memory Track (Stop boundary is always excluded!)</div>
          <div class="track" id="cell-track"></div>
        </div>
        
        <div class="output-box">
          <span>Printed Loop Values: <b id="out-values">[ ]</b></span>
          <span id="iter-count" style="color:#94a3b8; font-size:11.5px;">Iterations: 0</span>
        </div>
        
        <div class="rule-note">
          <span>💡</span> <b>Golden Rule:</b> The loop terminates strictly <i>before</i> reaching the red <span style="color:#ef4444; font-weight:bold;">STOP</span> boundary. Stop index 6 is never printed!
        </div>
      </div>

      <script>
        let curStart = 1, curStop = 6, curStep = 2;
        let yieldedList = [];
        let curVal = null;
        let simTimer = null;

        function refreshInputs() {
          curStart = parseInt(document.getElementById('in-start').value) || 0;
          curStop = parseInt(document.getElementById('in-stop').value) || 1;
          curStep = parseInt(document.getElementById('in-step').value) || 1;
          if (curStep <= 0) curStep = 1;
          
          document.getElementById('disp-start').innerText = curStart;
          document.getElementById('disp-stop').innerText = curStop;
          document.getElementById('disp-step').innerText = curStep;
        }

        function buildTrack() {
          refreshInputs();
          const track = document.getElementById('cell-track');
          track.innerHTML = '';
          const maxCells = Math.min(Math.max(curStop + 2, 8), 16);

          for (let i = 0; i < maxCells; i++) {
            const el = document.createElement('div');
            el.className = 'cell';
            el.id = 'cell-' + i;
            
            if (i === curStop) {
              el.classList.add('excluded');
            }
            
            el.innerHTML = `<span>${i}</span><span class="idx">i=${i}</span>`;
            track.appendChild(el);
          }
        }

        function resetSim() {
          if (simTimer) clearInterval(simTimer);
          yieldedList = [];
          curVal = curStart;
          document.querySelectorAll('.cell').forEach(c => {
            c.classList.remove('active', 'yielded');
          });
          document.getElementById('out-values').innerText = '[ ]';
          document.getElementById('iter-count').innerText = 'Iterations: 0';
        }

        function stepOnce() {
          refreshInputs();
          if (curVal === null || curVal < curStart || curVal >= curStop) {
            resetSim();
          }

          if (curVal < curStop) {
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('active'));
            const cEl = document.getElementById('cell-' + curVal);
            if (cEl) {
              cEl.classList.add('active');
              cEl.classList.add('yielded');
            }
            yieldedList.push(curVal);
            document.getElementById('out-values').innerText = '[ ' + yieldedList.join(', ') + ' ]';
            document.getElementById('iter-count').innerText = 'Iterations: ' + yieldedList.length;
            curVal += curStep;
          } else {
            // Finished
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('active'));
            if (simTimer) clearInterval(simTimer);
          }
        }

        function runSimulation() {
          resetSim();
          buildTrack();
          simTimer = setInterval(() => {
            if (curVal < curStop) {
              stepOnce();
            } else {
              clearInterval(simTimer);
              document.querySelectorAll('.cell').forEach(c => c.classList.remove('active'));
            }
          }, 600);
        }

        document.getElementById('in-start').addEventListener('change', () => { resetSim(); buildTrack(); });
        document.getElementById('in-stop').addEventListener('change', () => { resetSim(); buildTrack(); });
        document.getElementById('in-step').addEventListener('change', () => { resetSim(); buildTrack(); });

        buildTrack();
      </script>
    </body>
    </html>
    """

def render_while_loop_html() -> str:
    """Returns self-contained HTML/CSS/JS for an interactive While Loop & State Mutation simulator."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: #0b0f19; color: #e2e8f0; padding: 12px; }
        .vis-card {
          background: #111827;
          border: 1px solid #1f2937;
          border-radius: 12px;
          padding: 18px;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .title { font-size: 14.5px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
        .badge { background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
        
        .sim-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
          margin-bottom: 14px;
        }
        .box {
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 8px;
          padding: 12px;
        }
        .code-box {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12.5px;
          line-height: 1.6;
          color: #94a3b8;
        }
        .active-line {
          background: rgba(56, 189, 248, 0.15);
          color: #38bdf8;
          font-weight: bold;
          border-left: 3px solid #38bdf8;
          padding-left: 6px;
        }
        .state-val {
          font-size: 28px;
          font-weight: 800;
          color: #38bdf8;
          text-align: center;
          margin: 10px 0;
        }
        .cond-badge {
          text-align: center;
          padding: 4px 8px;
          border-radius: 6px;
          font-weight: 700;
          font-size: 12px;
        }
        .cond-true { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
        .cond-false { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
        
        .danger-banner {
          background: rgba(239, 68, 68, 0.15);
          border: 1px solid #ef4444;
          border-radius: 8px;
          padding: 10px 12px;
          color: #fca5a5;
          font-size: 12px;
          margin-top: 10px;
          display: none;
        }
        .btn-act {
          background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
          border: none;
          color: white;
          padding: 6px 14px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 12px;
          cursor: pointer;
          margin-right: 8px;
        }
      </style>
    </head>
    <body>
      <div class="vis-card">
        <div class="header">
          <div class="title">
            <span>🔄</span> While Loop State Mutation & Guard Simulator
          </div>
          <span class="badge">Live Condition Check</span>
        </div>

        <div class="sim-grid">
          <div class="box code-box">
            <div>count = 0</div>
            <div id="l-while">while count &lt; 3:</div>
            <div id="l-print">&nbsp;&nbsp;&nbsp;&nbsp;print(count)</div>
            <div id="l-inc" style="color:#fbbf24;">&nbsp;&nbsp;&nbsp;&nbsp;count += 1&nbsp;&nbsp;# Crucial!</div>
            <div>print("Loop Complete!")</div>
          </div>
          <div class="box" style="display:flex; flex-direction:column; justify-content:center;">
            <div style="font-size:11px; text-transform:uppercase; color:#64748b; font-weight:700; text-align:center;">
              Variable State
            </div>
            <div class="state-val" id="count-disp">count = 0</div>
            <div id="cond-disp" class="cond-badge cond-true">Condition: 0 &lt; 3 (TRUE - Keep Looping)</div>
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <button class="btn-act" onclick="stepWhile(true)">⏭ Next Safe Step (count += 1)</button>
            <button class="btn-act" style="background:#b91c1c;" onclick="simulateBug()">⚠️ Simulate Bug (No Increment)</button>
            <button class="btn-act" style="background:#334155;" onclick="resetWhile()">Reset</button>
          </div>
          <span id="status-msg" style="font-size:12px; color:#94a3b8;">Click Step to watch condition update</span>
        </div>

        <div class="danger-banner" id="bug-alert">
          🚨 <b>INFINITE LOOP DETECTED!</b> Because 'count' was not mutated inside the loop body, '0 &lt; 3' is eternally True. Python will freeze!
        </div>
      </div>

      <script>
        let count = 0;
        function updateUI() {
          document.getElementById('count-disp').innerText = 'count = ' + count;
          const condBadge = document.getElementById('cond-disp');
          if (count < 3) {
            condBadge.className = 'cond-badge cond-true';
            condBadge.innerText = 'Condition: ' + count + ' < 3 (TRUE - Running)';
            document.getElementById('status-msg').innerText = 'Loop continues for next iteration';
          } else {
            condBadge.className = 'cond-badge cond-false';
            condBadge.innerText = 'Condition: ' + count + ' < 3 (FALSE - Exited Cleanly)';
            document.getElementById('status-msg').innerText = 'Loop terminated safely!';
          }
        }

        function stepWhile(withInc) {
          document.getElementById('bug-alert').style.display = 'none';
          if (count < 3) {
            if (withInc) count++;
            updateUI();
          } else {
            count = 0;
            updateUI();
          }
        }

        function simulateBug() {
          document.getElementById('bug-alert').style.display = 'block';
          document.getElementById('status-msg').innerText = 'Process pinned at 100% CPU!';
        }

        function resetWhile() {
          count = 0;
          document.getElementById('bug-alert').style.display = 'none';
          updateUI();
        }
      </script>
    </body>
    </html>
    """

def render_break_continue_html() -> str:
    """Returns self-contained HTML/CSS/JS for Loop Control (Break vs Continue) simulator."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: #0b0f19; color: #e2e8f0; padding: 12px; }
        .vis-card {
          background: #111827;
          border: 1px solid #1f2937;
          border-radius: 12px;
          padding: 18px;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .title { font-size: 14.5px; font-weight: 700; color: #a5b4fc; display: flex; align-items: center; gap: 8px; }
        .badge { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
        
        .code-strip {
          background: #090d16;
          border: 1px solid #1e293b;
          border-radius: 8px;
          padding: 10px 14px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 12.5px;
          color: #94a3b8;
          margin-bottom: 14px;
          line-height: 1.5;
        }
        .conveyor {
          display: flex;
          gap: 12px;
          background: #030712;
          border: 1px solid #1f2937;
          border-radius: 10px;
          padding: 16px;
          margin-bottom: 14px;
          align-items: center;
        }
        .item-node {
          width: 50px;
          height: 52px;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 14px;
          background: #1e293b;
          border: 1px solid #334155;
          color: #cbd5e1;
          transition: all 0.3s ease;
        }
        .item-node.passed { background: rgba(16, 185, 129, 0.2); border-color: #10b981; color: #34d399; }
        .item-node.skipped { background: rgba(245, 158, 11, 0.2); border-color: #fbbf24; color: #fbbf24; opacity: 0.6; }
        .item-node.stopped { background: rgba(239, 68, 68, 0.25); border-color: #ef4444; color: #f87171; }
        
        .btn-ctl {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
          color: white;
          padding: 6px 14px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 12px;
          cursor: pointer;
        }
        .note { font-size: 12px; color: #94a3b8; margin-top: 10px; }
      </style>
    </head>
    <body>
      <div class="vis-card">
        <div class="header">
          <div class="title">
            <span>⚡</span> Flow Control Track: break vs continue
          </div>
          <span class="badge">Visual Track</span>
        </div>

        <div class="code-strip">
          for x in [1, 2, 3, 4, 5]:<br>
          &nbsp;&nbsp;&nbsp;&nbsp;if x == 2: <span style="color:#fbbf24; font-weight:bold;">continue</span>&nbsp;&nbsp;# Skips 2<br>
          &nbsp;&nbsp;&nbsp;&nbsp;if x == 4: <span style="color:#ef4444; font-weight:bold;">break</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Cancels loop at 4<br>
          &nbsp;&nbsp;&nbsp;&nbsp;print(x)
        </div>

        <div class="conveyor">
          <div class="item-node passed">x=1<span style="font-size:9px; color:#34d399;">PRINT</span></div>
          <div class="item-node skipped">x=2<span style="font-size:9px; color:#fbbf24;">SKIP</span></div>
          <div class="item-node passed">x=3<span style="font-size:9px; color:#34d399;">PRINT</span></div>
          <div class="item-node stopped">x=4<span style="font-size:9px; color:#ef4444;">HALT</span></div>
          <div class="item-node" style="opacity:0.3;">x=5<span style="font-size:9px;">NEVER</span></div>
        </div>

        <div class="note">
          <b>Outcome:</b> Output is strictly <code>1</code> then <code>3</code>. Item <code>2</code> is skipped by <code>continue</code>, and loop terminates forever upon reaching <code>4</code> with <code>break</code>.
        </div>
      </div>
    </body>
    </html>
    """

def render_step_visualizer_html(steps: list[dict[str, str]]) -> str:
    """Returns self-contained HTML/CSS/JS for an interactive step-by-step visualizer with stepper, Previous/Next buttons, and progress bar."""
    import json
    steps_json = json.dumps(steps)
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        body {{ background: #0b0f19; color: #e2e8f0; padding: 12px; }}
        .vis-card {{
          background: #111827;
          border: 1px solid #1f2937;
          border-radius: 12px;
          padding: 18px;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
        .title {{ font-size: 14.5px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }}
        .badge {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }}

        .progress-track {{
          background: #1e293b;
          border-radius: 999px;
          height: 8px;
          width: 100%;
          overflow: hidden;
          margin-bottom: 16px;
        }}
        .progress-fill {{
          height: 100%;
          background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
          transition: width 0.3s ease;
          border-radius: 999px;
        }}

        .stepper-dots {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          position: relative;
        }}
        .dot-node {{
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: #1e293b;
          border: 2px solid #334155;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11.5px;
          font-weight: 700;
          color: #94a3b8;
          cursor: pointer;
          transition: all 0.25s ease;
          z-index: 1;
        }}
        .dot-node.active {{
          background: #0284c7;
          border-color: #38bdf8;
          color: #ffffff;
          transform: scale(1.15);
          box-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
        }}
        .dot-node.completed {{
          background: rgba(16, 185, 129, 0.2);
          border-color: #10b981;
          color: #34d399;
        }}

        .step-content {{
          background: #090d16;
          border: 1px solid #1e293b;
          border-radius: 10px;
          padding: 16px 18px;
          margin-bottom: 16px;
          min-height: 90px;
        }}
        .step-header {{
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 8px;
        }}
        .step-tag {{
          background: rgba(129, 140, 248, 0.15);
          color: #a5b4fc;
          font-size: 11px;
          font-weight: 700;
          padding: 2px 7px;
          border-radius: 4px;
          text-transform: uppercase;
        }}
        .step-title {{
          font-size: 15px;
          font-weight: 700;
          color: #f8fafc;
        }}
        .step-detail {{
          font-size: 13.5px;
          color: #cbd5e1;
          line-height: 1.6;
        }}

        .stepper-controls {{
          display: flex;
          justify-content: space-between;
          align-items: center;
        }}
        .btn-step {{
          background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
          border: none;
          color: white;
          padding: 7px 16px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 12.5px;
          cursor: pointer;
          transition: filter 0.2s, transform 0.1s;
        }}
        .btn-step:hover:not(:disabled) {{
          filter: brightness(1.15);
          transform: translateY(-1px);
        }}
        .btn-step:disabled {{
          background: #1e293b;
          color: #64748b;
          cursor: not-allowed;
          border: 1px solid #334155;
        }}
        .step-status {{
          font-size: 12px;
          color: #94a3b8;
          font-weight: 600;
        }}
      </style>
    </head>
    <body>
      <div class="vis-card">
        <div class="header">
          <div class="title">
            <span>📍</span> Interactive Step-by-Step Walkthrough
          </div>
          <span class="badge" id="step-badge">Step 1 of {len(steps)}</span>
        </div>

        <div class="progress-track">
          <div class="progress-fill" id="p-bar" style="width: 0%;"></div>
        </div>

        <div class="stepper-dots" id="dots-container"></div>

        <div class="step-content">
          <div class="step-header">
            <span class="step-tag" id="s-tag">Step 1</span>
            <h4 class="step-title" id="s-title"></h4>
          </div>
          <p class="step-detail" id="s-detail"></p>
        </div>

        <div class="stepper-controls">
          <button class="btn-step" id="btn-prev" onclick="prevStep()">⬅ Previous</button>
          <span class="step-status" id="s-status">Use buttons to navigate</span>
          <button class="btn-step" id="btn-next" onclick="nextStep()">Next ➡</button>
        </div>
      </div>

      <script>
        const stepsData = {steps_json};
        let curStep = 0;

        function buildDots() {{
          const container = document.getElementById('dots-container');
          container.innerHTML = '';
          stepsData.forEach((_, idx) => {{
            const dot = document.createElement('div');
            dot.className = 'dot-node';
            dot.id = 'dot-' + idx;
            dot.innerText = idx + 1;
            dot.onclick = () => {{ curStep = idx; renderStep(); }};
            container.appendChild(dot);
          }});
        }}

        function renderStep() {{
          const total = stepsData.length;
          if (total === 0) return;
          if (curStep < 0) curStep = 0;
          if (curStep >= total) curStep = total - 1;

          const s = stepsData[curStep];
          document.getElementById('s-tag').innerText = 'Step ' + (curStep + 1);
          document.getElementById('s-title').innerText = s.title || ('Step ' + (curStep + 1));
          document.getElementById('s-detail').innerText = s.detail || '';
          document.getElementById('step-badge').innerText = 'Step ' + (curStep + 1) + ' of ' + total;

          const pct = Math.round(((curStep + 1) / total) * 100);
          document.getElementById('p-bar').style.width = pct + '%';

          document.getElementById('btn-prev').disabled = (curStep === 0);
          const nextBtn = document.getElementById('btn-next');
          if (curStep === total - 1) {{
            nextBtn.innerText = 'Completed ✓';
            nextBtn.disabled = true;
          }} else {{
            nextBtn.innerText = 'Next ➡';
            nextBtn.disabled = false;
          }}

          stepsData.forEach((_, idx) => {{
            const d = document.getElementById('dot-' + idx);
            if (d) {{
              d.className = 'dot-node';
              if (idx < curStep) d.classList.add('completed');
              else if (idx === curStep) d.classList.add('active');
            }}
          }});
        }}

        function nextStep() {{
          if (curStep < stepsData.length - 1) {{
            curStep++;
            renderStep();
          }}
        }}

        function prevStep() {{
          if (curStep > 0) {{
            curStep--;
            renderStep();
          }}
        }}

        buildDots();
        renderStep();
      </script>
    </body>
    </html>
    """


def render_animation(params: Union[dict, str, None]) -> None:
    """
    Renders an interactive animated component in Streamlit.
    Accepts:
    - params: dict, e.g. {"component": "range_viz", "start": 0, "end": 5}
    - params: dict, e.g. {"component": "step_viz", "steps": [{"title": "...", "detail": "..."}]}
    - params: str, e.g. "range_visualizer", "while_loop", "break_continue", "step_viz"
    If the component is unknown or steps are missing/invalid, shows nothing instead of crashing.
    """
    if not params:
        return

    start = 0
    end = 5
    step = 1

    if isinstance(params, dict):
        component_name = str(params.get("component") or "").lower().strip()
        start = int(params.get("start", 0))
        end = int(params.get("end", params.get("stop", 5)))
        step = int(params.get("step", 1))
    elif isinstance(params, str):
        component_name = params.lower().strip()
    else:
        return

    if "step" in component_name:
        steps = None
        if isinstance(params, dict):
            steps = params.get("steps")
        if not steps or not isinstance(steps, (list, tuple)) or len(steps) == 0:
            return
        valid_steps = []
        for s in steps:
            if isinstance(s, dict) and (s.get("title") or s.get("detail")):
                valid_steps.append({
                    "title": str(s.get("title") or f"Step {len(valid_steps) + 1}"),
                    "detail": str(s.get("detail") or ""),
                })
        if len(valid_steps) == 0:
            return
        try:
            html = render_step_visualizer_html(valid_steps)
            components.html(html, height=330, scrolling=False)
        except Exception:
            return
    elif "range" in component_name:
        try:
            from visualizer import render_range_visualizer
            components.html(render_range_visualizer(start=start, stop=end, step=step), height=380, scrolling=False)
        except Exception:
            components.html(render_range_visualizer_html(), height=360, scrolling=False)
    elif "while" in component_name or "infinite" in component_name:
        components.html(render_while_loop_html(), height=320, scrolling=False)
    elif "break" in component_name or "continue" in component_name or "control" in component_name:
        components.html(render_break_continue_html(), height=320, scrolling=False)
    else:
        # If the component is unknown, show nothing instead of crashing
        return

