import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getRuns } from '../api/client.js';

function RunsList() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    getRuns()
      .then((data) => {
        if (!cancelled) {
          setRuns(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Failed to load runs');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <div style={{ padding: '24px' }}>Loading runs...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: '24px', color: 'red' }}>Error: {error}</div>
    );
  }

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      <h1 style={{ marginBottom: '16px' }}>Eval Runs</h1>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px',
        }}
      >
        <thead>
          <tr style={{ borderBottom: '2px solid #333', textAlign: 'left' }}>
            <th style={{ padding: '8px' }}>Run Name</th>
            <th style={{ padding: '8px' }}>Model</th>
            <th style={{ padding: '8px' }}>Date</th>
            <th style={{ padding: '8px' }}>Total</th>
            <th style={{ padding: '8px' }}>Passed</th>
            <th style={{ padding: '8px' }}>Failed</th>
            <th style={{ padding: '8px' }}>Pass Rate</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const passRate =
              run.total_cases > 0
                ? `${((run.passed / run.total_cases) * 100).toFixed(1)}%`
                : '—';
            const date = new Date(run.created_at).toLocaleString();
            return (
              <tr
                key={run.id}
                onClick={() => navigate(`/runs/${run.id}`)}
                style={{
                  borderBottom: '1px solid #ddd',
                  cursor: 'pointer',
                }}
              >
                <td style={{ padding: '8px' }}>{run.run_name}</td>
                <td style={{ padding: '8px' }}>{run.model_name}</td>
                <td style={{ padding: '8px' }}>{date}</td>
                <td style={{ padding: '8px' }}>{run.total_cases}</td>
                <td style={{ padding: '8px', color: 'green' }}>{run.passed}</td>
                <td style={{ padding: '8px', color: 'red' }}>{run.failed}</td>
                <td style={{ padding: '8px' }}>{passRate}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default RunsList;
