import React from 'react'
import Plot from 'react-plotly.js'
import type { AnalysisResponse } from '../types'
import { POPULATION_LABELS } from '../types'

interface Props {
  data:      AnalysisResponse
  chartType: 'histogram' | 'boxplot'
}

export const Charts: React.FC<Props> = ({ data, chartType }) => {
  const populations = chartType === 'histogram'
    ? data.histogram_data.map(d => d.population)
    : data.boxplot_data.map(d => d.population)

  const plotTitle = chartType === 'histogram'
    ? 'Relative Frequency Distribution by Cell Population'
    : 'Relative Frequency Boxplot by Cell Population'

  if (chartType === 'histogram') {
    const traces: Plotly.Data[] = []

    for (const popData of data.histogram_data) {
      for (const g of popData.groups) {
        traces.push({
          type:        'histogram',
          x:           g.values,
          name:        `${g.label} — ${POPULATION_LABELS[popData.population] ?? popData.population}`,
          marker:      { color: g.color },
          opacity:     data.histogram_data[0].groups.length > 1 ? 0.6 : 0.85,
          xaxis:       `x${populations.indexOf(popData.population) > 0 ? populations.indexOf(popData.population) + 1 : ''}`,
          yaxis:       `y${populations.indexOf(popData.population) > 0 ? populations.indexOf(popData.population) + 1 : ''}`,
          legendgroup: g.label,
          showlegend:  populations.indexOf(popData.population) === 0,
          nbinsx:      20,
          histnorm:    'count',
        } as Plotly.Data)
      }
    }

    const n = populations.length
    const layout: Partial<Plotly.Layout> = {
      title:       { text: plotTitle, font: { color: '#fff', family: 'DM Serif Display', size: 16 } },
      paper_bgcolor: '#0a0a0a',
      plot_bgcolor:  '#111',
      font:         { color: '#ccc', family: 'DM Sans' },
      barmode:      'overlay',
      legend:       { bgcolor: '#1a1a1a', bordercolor: '#333', borderwidth: 1 },
      grid:         { rows: 1, columns: n, pattern: 'independent' },
      ...Object.fromEntries(populations.flatMap((pop, i) => {
        const axis = i === 0 ? '' : String(i + 1)
        return [
          [`xaxis${axis}`, { title: { text: `${POPULATION_LABELS[pop] ?? pop} (%)`, font: { color: '#aaa', size: 11 } }, gridcolor: '#222', zerolinecolor: '#333', tickfont: { color: '#888' } }],
          [`yaxis${axis}`, { title: { text: i === 0 ? 'Count' : '', font: { color: '#aaa', size: 11 } }, gridcolor: '#222', zerolinecolor: '#333', tickfont: { color: '#888' } }],
        ]
      })),
      height: 380,
      margin: { t: 50, b: 60, l: 50, r: 20 },
    }

    return (
      <Plot
        data={traces}
        layout={layout}
        config={{ displayModeBar: true, responsive: true }}
        style={{ width: '100%' }}
      />
    )
  }

  // Boxplot
  const traces: Plotly.Data[] = []
  for (const popData of data.boxplot_data) {
    for (const g of popData.groups) {
      traces.push({
        type:        'box',
        y:           g.values,
        name:        g.label,
        x:           Array(g.values.length).fill(POPULATION_LABELS[popData.population] ?? popData.population),
        marker:      { color: g.color },
        line:        { color: g.color },
        fillcolor:   g.color + '44',
        opacity:     data.boxplot_data[0].groups.length > 1 ? 0.75 : 0.9,
        legendgroup: g.label,
        showlegend:  data.boxplot_data.indexOf(popData) === 0,
        boxmean:     true,
      } as Plotly.Data)
    }
  }

  const layout: Partial<Plotly.Layout> = {
    title:         { text: plotTitle, font: { color: '#fff', family: 'DM Serif Display', size: 16 } },
    paper_bgcolor: '#0a0a0a',
    plot_bgcolor:  '#111',
    font:          { color: '#ccc', family: 'DM Sans' },
    boxmode:       'group',
    yaxis:         { title: { text: 'Relative Frequency (%)', font: { color: '#aaa', size: 12 } }, gridcolor: '#222', zerolinecolor: '#333', tickfont: { color: '#888' } },
    xaxis:         { gridcolor: '#222', tickfont: { color: '#ccc', size: 12 } },
    legend:        { bgcolor: '#1a1a1a', bordercolor: '#333', borderwidth: 1 },
    height:        420,
    margin:        { t: 50, b: 60, l: 60, r: 20 },
  }

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ displayModeBar: true, responsive: true }}
      style={{ width: '100%' }}
    />
  )
}
