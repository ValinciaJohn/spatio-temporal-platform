import time
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
from state_store import get_state

app = Dash(
    __name__,
    title="Traffic Intelligence Platform",
    suppress_callback_exceptions=True
)

REGIME_COLORS = {
    'free_flow': '#00C896',
    'slow':      '#F59E0B',
    'congested': '#F97316',
    'gridlock':  '#EF4444',
    'unknown':   '#6B7280',
}
STATE_COLORS = {
    'BORN':      '#34D399',
    'GROWING':   '#60A5FA',
    'STABLE':    '#94A3B8',
    'SHRINKING': '#FB923C',
    'DEAD':      '#F87171',
}

BG_BASE  = '#0A0F1E'
BG_PANEL = '#0F1929'
BG_CARD  = '#111827'
BORDER   = '#1E2D40'
TEXT_PRI = '#E2E8F0'
TEXT_SEC = '#64748B'
ACCENT   = '#38BDF8'
MONO     = '"Courier New", monospace'


def panel(title_text, icon, children):
    return html.Div([
        html.Div([
            html.Span(icon, style={'marginRight': '8px'}),
            html.Span(title_text, style={
                'fontWeight': '600', 'fontSize': '12px',
                'color': ACCENT, 'letterSpacing': '1px',
                'textTransform': 'uppercase',
            }),
        ], style={
            'marginBottom': '12px', 'paddingBottom': '10px',
            'borderBottom': f'1px solid {BORDER}',
            'display': 'flex', 'alignItems': 'center',
        }),
        children,
    ], style={
        'background': BG_PANEL, 'borderRadius': '12px',
        'padding': '16px 18px', 'marginBottom': '14px',
        'border': f'1px solid {BORDER}',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.4)',
    })


def stat_card(label, value, color=ACCENT):
    return html.Div([
        html.Div(str(value), style={
            'fontSize': '22px', 'fontWeight': '700',
            'color': color, 'lineHeight': '1.1', 'fontFamily': MONO,
        }),
        html.Div(label, style={
            'fontSize': '10px', 'color': TEXT_SEC,
            'textTransform': 'uppercase', 'letterSpacing': '1.2px',
            'marginTop': '4px',
        }),
    ], style={
        'background': BG_CARD, 'border': f'1px solid {BORDER}',
        'borderRadius': '10px', 'padding': '12px 14px',
        'minWidth': '100px', 'textAlign': 'center',
    })


app.layout = html.Div([

    dcc.Interval(id='timer', interval=5000, n_intervals=0),

    # ── Header ────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span('🚦', style={'fontSize': '20px', 'marginRight': '10px'}),
            html.Span('Traffic Intelligence Platform', style={
                'fontSize': '18px', 'fontWeight': '700', 'color': TEXT_PRI,
            }),
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Span('● LIVE', style={
            'color': '#34D399', 'fontWeight': '700',
            'fontSize': '12px', 'letterSpacing': '3px', 'fontFamily': MONO,
        }),
    ], style={
        'background': '#060D18', 'padding': '13px 28px',
        'display': 'flex', 'justifyContent': 'space-between',
        'alignItems': 'center', 'borderBottom': f'1px solid {BORDER}',
    }),

    # ── Stats Bar ─────────────────────────────────────────────────────────
    html.Div(id='stats-bar', style={
        'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap',
        'padding': '12px 24px', 'background': BG_BASE,
        'borderBottom': f'1px solid {BORDER}',
    }),

    # ── Main Grid ─────────────────────────────────────────────────────────
    html.Div([

        # LEFT — Map + Table
        html.Div([
            panel('Live Congestion Map', '📍',
                html.Iframe(id='map-iframe', style={
                    'width': '100%', 'height': '400px',
                    'border': 'none', 'borderRadius': '8px',
                    'background': BG_BASE,
                })
            ),
            panel('Cluster Intelligence Table', '📊',
                dash_table.DataTable(
                    id='cluster-table',
                    columns=[
                        {'name': 'ID',          'id': 'cluster_id'},
                        {'name': 'Size',        'id': 'size'},
                        {'name': 'Regime',      'id': 'regime'},
                        {'name': 'Hotspot',     'id': 'is_hotspot'},
                        {'name': 'Next Regime', 'id': 'predicted'},
                        {'name': 'Avg Speed',   'id': 'avg_speed'},
                        {'name': 'Lat',         'id': 'centroid_lat'},
                        {'name': 'Lon',         'id': 'centroid_lon'},
                    ],
                    data=[],
                    style_table={'overflowX': 'auto', 'borderRadius': '8px'},
                    style_header={
                        'backgroundColor': '#060D18', 'color': ACCENT,
                        'fontWeight': '600', 'fontSize': '11px',
                        'textAlign': 'center', 'padding': '10px',
                        'borderBottom': f'1px solid {BORDER}',
                        'textTransform': 'uppercase', 'letterSpacing': '0.8px',
                    },
                    style_cell={
                        'textAlign': 'center', 'fontSize': '12px',
                        'padding': '9px 12px', 'fontFamily': MONO,
                        'backgroundColor': BG_PANEL, 'color': TEXT_PRI,
                        'border': f'1px solid {BORDER}',
                    },
                    style_data_conditional=[
                        {'if': {'filter_query': '{regime} = "gridlock"'},
                         'backgroundColor': '#2D0A0A', 'color': '#FCA5A5', 'fontWeight': '700'},
                        {'if': {'filter_query': '{regime} = "congested"'},
                         'backgroundColor': '#1F1208', 'color': '#FDBA74'},
                        {'if': {'filter_query': '{regime} = "slow"'},
                         'backgroundColor': '#1C1A06', 'color': '#FDE68A'},
                        {'if': {'filter_query': '{regime} = "free_flow"'},
                         'backgroundColor': '#071A13', 'color': '#6EE7B7'},
                        {'if': {'filter_query': '{predicted} = "gridlock"'},
                         'color': '#FCA5A5'},
                        {'if': {'filter_query': '{predicted} = "congested"'},
                         'color': '#FDBA74'},
                        {'if': {'filter_query': '{predicted} = "slow"'},
                         'color': '#FDE68A'},
                        {'if': {'filter_query': '{is_hotspot} contains "YES"'},
                         'borderLeft': '3px solid #EF4444'},
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#0A1520'},
                    ],
                    page_size=10, sort_action='native',
                )
            ),
        ], style={'flex': '1', 'minWidth': '0'}),

        # RIGHT — Alerts + Regime + Drift + Evolution
        html.Div([

            panel('Anomaly & Alert Feed', '🚨',
                html.Div(id='alert-feed', style={
                    'height': '150px', 'overflowY': 'auto',
                    'background': BG_BASE, 'border': f'1px solid {BORDER}',
                    'borderRadius': '8px', 'padding': '10px 12px',
                    'fontSize': '12px', 'fontFamily': MONO, 'lineHeight': '1.7',
                })
            ),

            panel('Predicted Next Regime', '🔮',
                dcc.Graph(id='regime-chart', style={'height': '185px'},
                          config={'displayModeBar': False})
            ),

            # ── DRIFT DETECTION PANEL ─────────────────────────────────────
            panel('Drift Detection', '🌊', html.Div([
                # Stability gauge row
                html.Div(id='drift-status', style={
                    'display': 'flex', 'alignItems': 'center',
                    'gap': '12px', 'marginBottom': '10px',
                }),
                # Drift event log
                html.Div(id='drift-log', style={
                    'height': '100px', 'overflowY': 'auto',
                    'background': BG_BASE, 'border': f'1px solid {BORDER}',
                    'borderRadius': '8px', 'padding': '8px 12px',
                    'fontSize': '11px', 'fontFamily': MONO, 'lineHeight': '1.7',
                }),
            ])),

            panel('Cluster Evolution Log', '📈',
                html.Div(id='evolution-log', style={
                    'height': '200px', 'overflowY': 'auto',
                    'background': BG_BASE, 'border': f'1px solid {BORDER}',
                    'borderRadius': '8px', 'padding': '10px 12px',
                    'fontSize': '12px', 'fontFamily': MONO, 'lineHeight': '1.8',
                })
            ),

        ], style={'width': '380px', 'flexShrink': '0'}),

    ], style={
        'display': 'flex', 'gap': '14px', 'padding': '14px 24px',
        'alignItems': 'flex-start', 'background': BG_BASE,
        'minHeight': 'calc(100vh - 115px)',
    }),

], style={
    'fontFamily': '"Segoe UI", Arial, sans-serif',
    'background': BG_BASE, 'minHeight': '100vh', 'color': TEXT_PRI,
})


# ── CALLBACKS ─────────────────────────────────────────────────────────────────

@app.callback(Output('stats-bar', 'children'), Input('timer', 'n_intervals'))
def update_stats(n):
    clusters  = get_state('cluster_summary') or []
    scores    = get_state('eval_scores')     or {}
    anomalies = get_state('anomalies')       or []
    n_batches = get_state('total_batches')   or 0
    last_upd  = get_state('last_updated')    or 0
    drift_evs = get_state('drift_events')    or []

    n_clusters  = len(clusters)
    n_hotspots  = sum(1 for c in clusters if c.get('is_hotspot', False))
    n_anomalies = len(anomalies)
    n_drifts    = len(drift_evs)

    sil   = scores.get('silhouette', '--')
    db    = scores.get('db_index',   '--')
    stab  = scores.get('stability',  '--')
    noise = scores.get('noise_pct',  '--')

    sil_color = '#34D399' if isinstance(sil, float) and sil > 0.3 else \
                '#F59E0B' if isinstance(sil, float) and sil > 0  else \
                '#EF4444' if isinstance(sil, float) else TEXT_SEC

    stab_val = scores.get('stability_now', stab)
    stab_color = '#34D399' if isinstance(stab_val, float) and stab_val > 0.7 else \
                 '#F59E0B' if isinstance(stab_val, float) and stab_val > 0.4 else \
                 '#EF4444' if isinstance(stab_val, float) else TEXT_SEC

    upd_str = time.strftime('%H:%M:%S', time.localtime(last_upd)) if last_upd else '--'
    fmt = lambda v: round(v, 4) if isinstance(v, float) else v

    return [
        stat_card('Clusters',   n_clusters,  ACCENT),
        stat_card('Hotspots',   n_hotspots,  '#EF4444'),
        stat_card('Anomalies',  n_anomalies, '#F97316'),
        stat_card('Batches',    n_batches,   '#34D399'),
        stat_card('Drift Events', n_drifts,  '#A78BFA'),
        stat_card('Silhouette', fmt(sil),    sil_color),
        stat_card('Stability',  fmt(stab_val), stab_color),
        stat_card('Noise %',    fmt(noise),  TEXT_SEC),
        stat_card('Updated',    upd_str,     TEXT_SEC),
    ]


@app.callback(Output('map-iframe', 'srcDoc'), Input('timer', 'n_intervals'))
def update_map(n):
    try:
        with open('live_map.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ('<html><body style="margin:0;background:#0A0F1E;display:flex;'
                'align-items:center;justify-content:center;height:100%;">'
                '<p style="color:#64748B;font-family:monospace;">🗺️ Waiting for map...</p>'
                '</body></html>')


@app.callback(Output('cluster-table', 'data'), Input('timer', 'n_intervals'))
def update_table(n):
    summary = get_state('cluster_summary') or []
    return [{
        'cluster_id':   row.get('cluster_id', '?'),
        'size':         row.get('size', 0),
        'regime':       row.get('regime', 'unknown'),
        'is_hotspot':   '🔴 YES' if row.get('is_hotspot') else '—',
        'predicted':    row.get('predicted', '--'),
        'avg_speed':    row.get('avg_speed', '--'),
        'centroid_lat': row.get('centroid_lat', '--'),
        'centroid_lon': row.get('centroid_lon', '--'),
    } for row in summary]


@app.callback(Output('alert-feed', 'children'), Input('timer', 'n_intervals'))
def update_alerts(n):
    alerts = get_state('alerts') or []
    if not alerts:
        return html.Div('✅  No alerts. System nominal.',
                        style={'color': '#34D399', 'padding': '6px'})
    return [
        html.Div(a, style={
            'color': '#EF4444' if '🔴' in a else
                     '#F97316' if '⚠'  in a else
                     '#F59E0B' if '🟡' in a else
                     '#A78BFA' if '🔵' in a else '#60A5FA',
            'padding': '3px 0',
            'borderBottom': f'1px solid {BORDER}',
        })
        for a in reversed(alerts[-15:])
    ]


@app.callback(Output('regime-chart', 'figure'), Input('timer', 'n_intervals'))
def update_regime_chart(n):
    summary = get_state('cluster_summary') or []
    if not summary:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text='Waiting for data...', font=dict(color=TEXT_SEC, size=12)),
            plot_bgcolor=BG_PANEL, paper_bgcolor=BG_PANEL, height=170,
        )
        return fig

    items       = summary[:12]
    cluster_ids = [str(r.get('cluster_id', '?')) for r in items]
    regimes     = [r.get('predicted') or r.get('regime', 'unknown') for r in items]
    colors      = [REGIME_COLORS.get(r, '#6B7280') for r in regimes]

    fig = go.Figure(go.Bar(
        x=cluster_ids, y=[1]*len(cluster_ids),
        marker_color=colors, marker_line_width=0,
        text=regimes, textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='white', size=9),
    ))
    fig.update_layout(
        xaxis=dict(
            title='Cluster ID',
            title_font=dict(color=TEXT_SEC, size=11),
            tickfont=dict(color=TEXT_SEC, size=10),
            gridcolor=BORDER,
        ),
        yaxis_visible=False,
        plot_bgcolor=BG_PANEL, paper_bgcolor=BG_PANEL,
        margin=dict(l=8, r=8, t=8, b=40),
        height=170, showlegend=False, bargap=0.15,
    )
    return fig


@app.callback(
    Output('drift-status', 'children'),
    Output('drift-log', 'children'),
    Input('timer', 'n_intervals')
)
def update_drift_panel(n):
    scores      = get_state('eval_scores')  or {}
    drift_evs   = get_state('drift_events') or []

    stability   = scores.get('stability_now', scores.get('stability', None))

    # ── Stability indicator ───────────────────────────────────────────────
    if stability is None:
        stab_color = TEXT_SEC
        stab_label = 'Waiting...'
        stab_icon  = '⏳'
    elif stability > 0.7:
        stab_color = '#34D399'
        stab_label = f'STABLE  {round(stability, 3)}'
        stab_icon  = '✅'
    elif stability > 0.4:
        stab_color = '#F59E0B'
        stab_label = f'UNSTABLE  {round(stability, 3)}'
        stab_icon  = '⚠️'
    else:
        stab_color = '#EF4444'
        stab_label = f'DRIFTING  {round(stability, 3)}'
        stab_icon  = '🌊'

    status_children = [
        html.Span(stab_icon, style={'fontSize': '18px'}),
        html.Div([
            html.Div('Pattern Stability', style={
                'fontSize': '10px', 'color': TEXT_SEC,
                'textTransform': 'uppercase', 'letterSpacing': '1px',
            }),
            html.Div(stab_label, style={
                'fontSize': '15px', 'fontWeight': '700',
                'color': stab_color, 'fontFamily': MONO,
            }),
        ]),
        html.Div([
            html.Div('Drift Events', style={
                'fontSize': '10px', 'color': TEXT_SEC,
                'textTransform': 'uppercase', 'letterSpacing': '1px',
            }),
            html.Div(str(len(drift_evs)), style={
                'fontSize': '15px', 'fontWeight': '700',
                'color': '#A78BFA', 'fontFamily': MONO,
            }),
        ], style={'marginLeft': 'auto'}),
    ]

    # ── Drift event log ───────────────────────────────────────────────────
    if not drift_evs:
        log_children = html.Div(
            '✅  No drift detected. Traffic patterns stable.',
            style={'color': '#34D399', 'padding': '4px'}
        )
    else:
        log_children = [
            html.Div(
                f"🌊  [{e.get('time_str', '??:??:??')}]  "
                f"Pattern drift — {e.get('n_clusters', '?')} clusters re-formed",
                style={
                    'color': '#A78BFA', 'padding': '2px 0',
                    'borderBottom': f'1px solid {BORDER}',
                }
            )
            for e in reversed(drift_evs[-10:])
        ]

    return status_children, log_children


@app.callback(Output('evolution-log', 'children'), Input('timer', 'n_intervals'))
def update_evolution_log(n):
    log = get_state('evolution_log') or []
    if not log:
        return html.Div('Waiting for evolution data...',
                        style={'color': TEXT_SEC, 'padding': '8px', 'fontStyle': 'italic'})
    return [
        html.Div(
            event.get('text', str(event)) if isinstance(event, dict) else str(event),
            style={
                'color': STATE_COLORS.get(
                    event.get('state', 'STABLE') if isinstance(event, dict) else 'STABLE',
                    TEXT_SEC
                ),
                'padding': '3px 0',
                'borderBottom': f'1px solid {BORDER}',
            }
        )
        for event in reversed(log[-30:])
    ]


if __name__ == '__main__':
    print('[DASHBOARD] Starting at http://localhost:8050')
    app.run(debug=False, port=8050)