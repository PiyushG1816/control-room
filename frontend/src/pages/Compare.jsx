import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getCompare, getRuns } from '../api/client.js';

const STATUS_COLORS = {
  regression: 'red',
  improvement: 'green',
  unchanged: 'gray',
};

function passFailBadge(passed) {
  return {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    color: 'white',
    backgroundColor: passed ? 'green' : 'red',
    fontWeight: 'bold',
    fontSize: '12px',
  };
}

function statusBadge(status) {
  return {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    color: 'white',
    backgroundColor: STATUS_COLORS[status] || 'gray',
    fontWeight: 'bold',
    fontSize: '12px',
  };
}

function Compare() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const urlRunA = searchParams.get('run_a') || '';
  const urlRunB = searchParams.get('run_b') || '';

  const [runs, setRuns] = useState([]);
  const [selectedA, setSelectedA] = useState(urlRunA);
  const [selectedB, setSelectedB] = useState(urlRunB);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getRuns()
      .then((data) => {
        if (!cancelled) setRuns(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Failed to load runs');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!urlRunA || !urlRunB) {
      setComparison(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getCompare(urlRunA, urlRunB)
      .then((data) => {
        if (!cancelled) {
          setComparison(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Failed to load comparison');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [urlRunA, urlRunB]);

  const handleCompare = () => {
    if (!selectedA || !selectedB) return;
    setSearchParams({ run_a: selectedA, run_b: selectedB });
  };

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

  const selectStyle = {
    padding: '6px 8px',
    fontSize: '14px',
    minWidth: '260px',
    marginRight: '8px',
  };

  return (
    <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
      {backButton}
      <h1 style={{ margin: '0 0 16px 0' }}>Compare Runs</h1>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '24px',
          flexWrap: 'wrap',
        }}
      >
        <label>
          Run A:{' '}
          <select
            value={selectedA}
            onChange={(e) => setSelectedA(e.target.value)}
            style={selectStyle}
          >
            <option value="">— Select Run A —</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                {run.run_name} ({run.model_name})
              </option>
            ))}
          </select>
        </label>
        <label>
          Run B:{' '}
          <select
            value={selectedB}
            onChange={(e) => setSelectedB(e.target.value)}
            style={selectStyle}
          >
            <option value="">— Select Run B —</option>
            {runs.map((run) => (
              <option key={run.id} value={run.id}>
                {run.run_name} ({run.model_name})
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={handleCompare}
          disabled={!selectedA || !selectedB}
          style={{
            padding: '6px 16px',
            fontSize: '14px',
            cursor:
              !selectedA || !selectedB ? 'not-allowed' : 'pointer',
            border: '1px solid #333',
            background: '#333',
            color: 'white',
            borderRadius: '4px',
          }}
        >
          Compare
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '16px' }}>
          Error: {error}
        </div>
      )}

      {loading && <div>Loading comparison...</div>}

      {!loading && comparison && (
        <>
          <div
            style={{
              padding: '16px',
              marginBottom: '24px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              background: '#fafafa',
            }}
          >
            <div style={{ marginBottom: '8px', fontSize: '16px' }}>
              <strong>{comparison.run_a.run_name}</strong>
              {' ('}
              {comparison.run_a.model_name}
              {') vs '}
              <strong>{comparison.run_b.run_name}</strong>
              {' ('}
              {comparison.run_b.model_name}
              {')'}
            </div>
            <div>
              <span style={{ color: 'red', marginRight: '16px' }}>
                <strong>Regressions:</strong>{' '}
                {comparison.summary.regressions}
              </span>
              <span style={{ color: 'green', marginRight: '16px' }}>
                <strong>Improvements:</strong>{' '}
                {comparison.summary.improvements}
              </span>
              <span style={{ color: 'gray', marginRight: '16px' }}>
                <strong>Unchanged:</strong>{' '}
                {comparison.summary.unchanged}
              </span>
              <span>
                <strong>Total compared:</strong>{' '}
                {comparison.summary.total_compared}
              </span>
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
              <tr
                style={{
                  borderBottom: '2px solid #333',
                  textAlign: 'left',
                }}
              >
                <th style={{ padding: '8px' }}>Input</th>
                <th style={{ padding: '8px' }}>Expected</th>
                <th style={{ padding: '8px' }}>Run A</th>
                <th style={{ padding: '8px' }}>Run B</th>
                <th style={{ padding: '8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {comparison.comparisons.map((entry, index) => (
                <tr
                  key={index}
                  style={{
                    borderBottom: '1px solid #eee',
                    verticalAlign: 'top',
                  }}
                >
                  <td style={{ padding: '8px' }}>{entry.input}</td>
                  <td style={{ padding: '8px' }}>{entry.expected}</td>
                  <td style={{ padding: '8px' }}>
                    <div style={{ marginBottom: '4px' }}>
                      <span style={passFailBadge(entry.result_a.passed)}>
                        {entry.result_a.passed ? 'PASS' : 'FAIL'}
                      </span>
                    </div>
                    <div>{entry.result_a.actual}</div>
                  </td>
                  <td style={{ padding: '8px' }}>
                    <div style={{ marginBottom: '4px' }}>
                      <span style={passFailBadge(entry.result_b.passed)}>
                        {entry.result_b.passed ? 'PASS' : 'FAIL'}
                      </span>
                    </div>
                    <div>{entry.result_b.actual}</div>
                  </td>
                  <td style={{ padding: '8px' }}>
                    <span style={statusBadge(entry.status)}>
                      {entry.status.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default Compare;
