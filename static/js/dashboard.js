/* EduMetrics dashboard: fetch analysis JSON, render KPIs + Plotly charts.
   Sections hide automatically when their columns were absent in the upload. */
async function main() {
  const res = await fetch('/api/dashboard-data');
  const j = await res.json();
  if (!j.ok) { window.location.href = '/upload'; return; }
  const { quality: q, summary: s, insights, recommendations, filename } = j;
  document.getElementById('loading').style.display = 'none';
  document.getElementById('dash').style.display = 'block';
  if (filename) document.getElementById('fname').textContent = filename;

  const BLUE = '#1d4ed8', RED = '#e11d48', TEAL = '#0d9488', GREEN = '#16a34a';
  const layout = (t) => ({ title: '', margin: { t: 10, l: 50, r: 10, b: 50 },
    autosize: true, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' });

  // ---------- KPIs (only when data exists) ----------
  const k = s.kpis, cards = [['TOTAL STUDENTS', k.total_students, 'students in file', '']];
  if (k.avg_score != null) cards.push(['AVERAGE SCORE', k.avg_score, `pass ≥ ${k.pass_mark}`, '']);
  if (k.avg_attendance != null) cards.push(['AVERAGE ATTENDANCE', k.avg_attendance + '%', 'target 80%+', 'red']);
  if (k.avg_study_hours != null) cards.push(['AVG STUDY HOURS', k.avg_study_hours, 'hours / week', '']);
  if (k.pass_pct != null) cards.push(['PASS RATE', k.pass_pct + '%', `pass ≥ ${k.pass_mark}`, '']);
  document.getElementById('kpis').innerHTML = cards.map(c =>
    `<div class="kpi ${c[3]}"><div class="label">${c[0]}</div><div class="value">${c[1]}</div><div class="hint">${c[2]}</div></div>`).join('');

  // ---------- data quality ----------
  const det = q.detected || {};
  document.getElementById('qtable').innerHTML =
    `<tr><th>Check</th><th>Value</th></tr>` +
    `<tr><td>Rows uploaded</td><td>${q.rows_uploaded}</td></tr>` +
    `<tr><td>Rows after cleaning</td><td>${q.rows_after}</td></tr>` +
    `<tr><td>Missing values found</td><td>${q.missing_values}</td></tr>` +
    `<tr><td>Duplicate rows removed</td><td>${q.duplicates_removed}</td></tr>` +
    `<tr><td>Numeric / categorical cols</td><td>${q.numeric_columns} / ${q.categorical_columns}</td></tr>`;
  document.getElementById('qcols').innerHTML =
    `<tr><th>Detected field</th><th>CSV column</th></tr>` +
    Object.entries(det).filter(([kk]) => !['subjects','final_derived','grade_derived'].includes(kk))
      .map(([kk, v]) => `<tr><td>${kk}</td><td>${v}</td></tr>`).join('') +
    `<tr><td>subjects</td><td>${(det.subjects || []).join(', ') || '—'}</td></tr>`;

  const H = s.has, C = s.charts;
  const hide = (id) => document.getElementById(id).style.display = 'none';

  // ---------- performance ----------
  if (!H.score) hide('secPerf');
  else {
    const p = s.stats.performance;
    document.getElementById('perfStats').textContent =
      `Mean ${p.mean} · median ${p.median} · SD ${p.std} · range ${p.min}–${p.max} · pass ${p.pass_pct}% (≥ ${p.pass_mark}).`;
    Plotly.newPlot('cScore', [{ x: C.scores, type: 'histogram', marker: { color: BLUE }, opacity: .8 }],
      { ...layout(), xaxis: { title: 'Final score' }, yaxis: { title: 'Students' } }, { responsive: true });
    if (C.grades) Plotly.newPlot('cGrade',
      [{ x: C.grades.labels, y: C.grades.values, type: 'bar', marker: { color: [GREEN, BLUE, TEAL, '#f59e0b', RED, '#991b1b'] } }],
      { ...layout(), xaxis: { title: 'Grade' }, yaxis: { title: 'Students' } }, { responsive: true });
    else document.getElementById('cGrade').innerHTML = '<p class="why">No grade column.</p>';
    if (C.subject_avgs && C.subject_avgs.labels.length)
      Plotly.newPlot('cSubj', [{ x: C.subject_avgs.labels, y: C.subject_avgs.values, type: 'bar', marker: { color: RED } }],
        { ...layout(), xaxis: { title: 'Subject' }, yaxis: { title: 'Mean score' } }, { responsive: true });
    else document.getElementById('subjWrap').style.display = 'none';
  }

  // ---------- attendance ----------
  if (!H.attendance) hide('secAtt');
  else {
    const a = s.stats.attendance;
    document.getElementById('attStats').textContent =
      `Mean ${a.mean}% · median ${a.median}% · SD ${a.std} · ${a.low_pct}% below 60% · ${a.high_pct}% above 80%.`;
    Plotly.newPlot('cAtt', [{ x: C.attendance, type: 'histogram', marker: { color: TEAL }, opacity: .8 }],
      { ...layout(), xaxis: { title: 'Attendance (%)' }, yaxis: { title: 'Students' } }, { responsive: true });
    Plotly.newPlot('cAttBand', [{ x: C.attendance_bands.labels, y: C.attendance_bands.values, type: 'bar', marker: { color: BLUE } }],
      { ...layout(), xaxis: { title: 'Band' }, yaxis: { title: 'Students' } }, { responsive: true });
    if (C.att_vs_score) {
      if (s.correlation_att_score != null) document.getElementById('rAtt').textContent = 'Correlation: ' + s.correlation_att_score;
      Plotly.newPlot('cAttScore',
        [{ x: C.att_vs_score.x, y: C.att_vs_score.y, mode: 'markers', type: 'scatter',
           marker: { color: BLUE, opacity: .45 }, name: 'students' }],
        { ...layout(), xaxis: { title: 'Attendance (%)' }, yaxis: { title: 'Final score' } }, { responsive: true });
      Plotly.newPlot('cAttMean', [{ x: C.att_band_means.labels, y: C.att_band_means.values, type: 'bar', marker: { color: GREEN } }],
        { ...layout(), xaxis: { title: 'Attendance band' }, yaxis: { title: 'Mean score' } }, { responsive: true });
    }
  }

  // ---------- study ----------
  if (!H.study) hide('secStudy');
  else {
    if (s.correlation_study_score != null) document.getElementById('rStu').textContent = 'Correlation: ' + s.correlation_study_score;
    if (C.study_vs_score) Plotly.newPlot('cStuScore',
      [{ x: C.study_vs_score.x, y: C.study_vs_score.y, mode: 'markers', type: 'scatter',
         marker: { color: RED, opacity: .45 } }],
      { ...layout(), xaxis: { title: 'Study hours / week' }, yaxis: { title: 'Final score' } }, { responsive: true });
    Plotly.newPlot('cStu', [{ x: C.study_hours, type: 'histogram', marker: { color: '#f59e0b' }, opacity: .85 }],
      { ...layout(), xaxis: { title: 'Study hours / week' }, yaxis: { title: 'Students' } }, { responsive: true });
  }

  // ---------- groups + heatmap ----------
  let groupsVisible = false;
  const G = s.groups || {};
  if (G.gender) { groupsVisible = true;
    Plotly.newPlot('cGender', [{ x: G.gender.labels, y: G.gender.values, type: 'bar', marker: { color: TEAL } }],
      { ...layout(), xaxis: { title: 'Gender' }, yaxis: { title: 'Mean score' } }, { responsive: true });
  } else document.getElementById('gWrap').style.display = 'none';
  if (G.test_prep) { groupsVisible = true;
    Plotly.newPlot('cPrep', [{ x: G.test_prep.labels, y: G.test_prep.values, type: 'bar', marker: { color: [GREEN, RED] } }],
      { ...layout(), xaxis: { title: 'Test preparation' }, yaxis: { title: 'Mean score' } }, { responsive: true });
  } else document.getElementById('pWrap').style.display = 'none';
  if (G.parental) { groupsVisible = true;
    Plotly.newPlot('cPar', [{ x: G.parental.labels, y: G.parental.values, type: 'bar', marker: { color: BLUE } }],
      { ...layout(), xaxis: { title: 'Parental education' }, yaxis: { title: 'Mean score' } }, { responsive: true });
  } else document.getElementById('parWrap').style.display = 'none';
  if (s.correlation) { groupsVisible = true;
    Plotly.newPlot('cHeat', [{ z: s.correlation.matrix, x: s.correlation.labels, y: s.correlation.labels,
      type: 'heatmap', colorscale: 'RdBu', zmin: -1, zmax: 1, reversescale: true }],
      { ...layout(), margin: { t: 10, l: 110, r: 10, b: 110 } }, { responsive: true });
  } else document.getElementById('heatWrap').style.display = 'none';
  if (!groupsVisible) hide('secGroups');

  // ---------- segmentation ----------
  if (!s.segments) hide('secSeg');
  else {
    document.getElementById('segCrit').textContent = 'Criteria: ' + s.segments.criteria + ' (auto-scaled for 0–10 GPA data).';
    document.getElementById('segTable').innerHTML =
      `<tr><th>Segment</th><th>Students</th><th>Share</th><th>Avg score</th><th>Avg attendance</th><th>Avg study h</th></tr>` +
      s.segments.rows.map(r => `<tr><td>${r.segment}</td><td>${r.count}</td><td>${r.pct}%</td>` +
        `<td>${r.avg_score}</td><td>${r.avg_attendance ?? '—'}</td><td>${r.avg_study ?? '—'}</td></tr>`).join('');
    if (C.att_vs_score) {
      // colour scatter points by segment using score thresholds
      const lo = s.segments.low, hi = s.segments.high;
      const col = C.att_vs_score.y.map(v => v < lo ? RED : (v >= hi ? GREEN : BLUE));
      Plotly.newPlot('cSeg', [{ x: C.att_vs_score.x, y: C.att_vs_score.y, mode: 'markers', type: 'scatter',
        marker: { color: col, opacity: .55 } }],
        { ...layout(), xaxis: { title: 'Attendance (%)' }, yaxis: { title: 'Final score' } }, { responsive: true });
      const bands = [[], [], []];
      C.att_vs_score.y.forEach(v => bands[v < lo ? 0 : (v >= hi ? 2 : 1)].push(v));
      Plotly.newPlot('cSegBox', [
        { y: bands[0], type: 'box', name: 'Needs Attention', marker: { color: RED } },
        { y: bands[1], type: 'box', name: 'Average', marker: { color: BLUE } },
        { y: bands[2], type: 'box', name: 'High', marker: { color: GREEN } }],
        { ...layout(), yaxis: { title: 'Final score' } }, { responsive: true });
    }
  }

  // ---------- insights / recommendations ----------
  document.getElementById('ins').innerHTML = insights.map(t => `<li>${t}</li>`).join('');
  document.getElementById('rec').innerHTML = recommendations.map(t => `<li>${t}</li>`).join('');
}
main().catch(() => { document.getElementById('loading').textContent = 'Failed to load. Upload a CSV first.'; });
