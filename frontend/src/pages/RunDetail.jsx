import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRun } from '../api/client.js';

function truncate(text, max = 60) {
  if (text == null) return '';
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function RunDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getRun(id)
      .then((data) => {
        if (!cancelled) {
          setRun(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Failed to load run');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const backButton = (
    <button
      onClick={() => navigate('/')}
      style={{
        padding: '6px 12px',
        marginBottom: '16px',
        cursor: 'pointer',
        border: '1px solid #888',
        background: '#f5f5f5',
        borderRadius: '4px',
      }}
    >
      &larr; Back
    </button>
  );

  if (loading) {
    return (
      <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
        {backButton}
        <div>Loading run...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
        {backButton}
        <div style={{ color: 'red' }}>Error: {error}</div>
      </div>
    );
  }

  const total = run.total_cases;
  const passRate =
    total > 0 ? `${((run.passed / total) * 100).toFixed(1)}%` : '—';
  const date = new Date(run.created_at).toLocaleString();

  const badgeStyle = (passed) => ({
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    color: 'white',
    backgroundColor: passed ? 'green' : 'red',
    fontWeight: 'bold',
    fontSize: '12px',
  });

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      {backButton}

      <div
        style={{
          padding: '16px',
          marginBottom: '24px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          background: '#fafafa',
        }}
      >
        <h1 style={{ margin: '0 0 8px 0' }}>{run.run_name}</h1>
        <div style={{ marginBottom: '4px' }}>
          <strong>Model:</strong> {run.model_name}
        </div>
        <div style={{ marginBottom: '4px' }}>
          <strong>Date:</strong> {date}
        </div>
        <div style={{ marginBottom: '4px' }}>
          <strong>Total:</strong> {total}
          {' | '}
          <span style={{ color: 'green' }}>
            <strong>Passed:</strong> {run.passed}
          </span>
          {' | '}
          <span style={{ color: 'red' }}>
            <strong>Failed:</strong> {run.failed}
          </span>
        </div>
        <div>
          <strong>Pass Rate:</strong> {passRate}
        </div>
      </div>

      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px',
        }}
      >
        <thead>
          <tr style={{ borderBottom: '2px solid #333', textAlign: 'left' }}>
            <th style={{ padding: '8px' }}>#</th>
            <th style={{ padding: '8px' }}>Input</th>
            <th style={{ padding: '8px' }}>Expected</th>
            <th style={{ padding: '8px' }}>Actual</th>
            <th style={{ padding: '8px' }}>Result</th>
            <th style={{ padding: '8px' }}>Confidence</th>
            <th style={{ padding: '8px' }}>Reasoning</th>
          </tr>
        </thead>
        <tbody>
          {run.results.map((result, index) => (
            <tr
              key={result.id}
              style={{ borderBottom: '1px solid #eee', verticalAlign: 'top' }}
            >
              <td style={{ padding: '8px' }}>{index + 1}</td>
              <td style={{ padding: '8px' }}>{truncate(result.input)}</td>
              <td style={{ padding: '8px' }}>{truncate(result.expected)}</td>
              <td style={{ padding: '8px' }}>{truncate(result.actual)}</td>
              <td style={{ padding: '8px' }}>
                <span style={badgeStyle(result.passed)}>
                  {result.passed ? 'PASS' : 'FAIL'}
                </span>
              </td>
              <td style={{ padding: '8px' }}>
                {(result.confidence * 100).toFixed(1)}%
              </td>
              <td style={{ padding: '8px' }}>{result.reasoning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RunDetail;
