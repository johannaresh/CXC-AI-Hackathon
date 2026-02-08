import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container } from '../components/layout/Container';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Spinner } from '../components/ui/Spinner';
import { apiService } from '../services/api';

interface Strategy {
  name: string;
  description: string;
  assets: string[];
  backtest_sharpe: number;
}

type Mode = 'quick-select' | 'manual';
type Step = 'mode' | 'strategy' | 'asset' | 'confirm';

export function SubmitAuditPage() {
  const navigate = useNavigate();

  // Mode selection
  const [mode, setMode] = useState<Mode | null>(null);
  const [step, setStep] = useState<Step>('mode');

  // Quick select state
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string>('');

  // Submission state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load strategies when quick-select mode is chosen
  useEffect(() => {
    if (mode === 'quick-select' && strategies.length === 0) {
      loadStrategies();
    }
  }, [mode]);

  const loadStrategies = async () => {
    setLoadingStrategies(true);
    setError(null);
    try {
      const response = await apiService.getStrategies();
      setStrategies(response.strategies || []);
      setStep('strategy');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategies');
      setMode(null);
      setStep('mode');
    } finally {
      setLoadingStrategies(false);
    }
  };

  const handleModeSelect = (selectedMode: Mode) => {
    setMode(selectedMode);
    if (selectedMode === 'quick-select') {
      // Will trigger useEffect to load strategies
    } else {
      // Manual mode not yet implemented - show error message
      setError('Manual entry mode is not yet implemented. Please use Quick Select.');
      setMode(null);
    }
  };

  const handleStrategySelect = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setStep('asset');
  };

  const handleAssetSelect = (asset: string) => {
    setSelectedAsset(asset);
    setStep('confirm');
  };

  const handleSubmit = async () => {
    if (!selectedStrategy) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Fetch full strategy data
      const strategyData = await apiService.getStrategyByName(selectedStrategy.name);

      // Add selected_asset to payload
      const payload = {
        ...strategyData,
        selected_asset: selectedAsset || undefined,
      };

      const result = await apiService.submitAudit(payload);

      setSuccess(`Audit submitted successfully! Audit ID: ${result.audit_id}`);

      // Navigate to the detail page after 1.5 seconds
      setTimeout(() => {
        navigate(`/audit/${result.audit_id}`);
      }, 1500);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit audit');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (step === 'confirm') {
      setStep('asset');
      setSelectedAsset('');
    } else if (step === 'asset') {
      setStep('strategy');
      setSelectedStrategy(null);
    } else if (step === 'strategy') {
      setStep('mode');
      setMode(null);
    }
  };

  return (
    <Container>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Submit New Audit</h1>
        <p className="mt-2 text-gray-600">
          Run a comprehensive edge analysis on your trading strategy
        </p>
      </div>

      {success && (
        <div className="mb-6 bg-success-50 border border-success-200 text-success-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Success!</p>
          <p className="text-sm">{success}</p>
          <p className="text-sm mt-1">Redirecting to audit results...</p>
        </div>
      )}

      {error && (
        <div className="mb-6">
          <ErrorMessage message={error} />
        </div>
      )}

      {/* Step 1: Mode Selection */}
      {step === 'mode' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <button
            onClick={() => handleModeSelect('quick-select')}
            className="bg-white p-8 rounded-lg shadow-md hover:shadow-lg transition-shadow border-2 border-transparent hover:border-primary-500 text-left"
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Quick Select
            </h3>
            <p className="text-gray-600 mb-4">
              Choose from pre-loaded strategies and select a specific asset to audit
            </p>
            <div className="flex items-center text-primary-600 font-medium">
              <span>Select Strategy →</span>
            </div>
          </button>

          <button
            onClick={() => handleModeSelect('manual')}
            className="bg-white p-8 rounded-lg shadow-md hover:shadow-lg transition-shadow border-2 border-transparent hover:border-primary-500 text-left"
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Manual Entry
            </h3>
            <p className="text-gray-600 mb-4">
              Enter your own strategy details and backtest metrics
            </p>
            <div className="flex items-center text-primary-600 font-medium">
              <span>Enter Details →</span>
            </div>
          </button>
        </div>
      )}

      {/* Step 2: Strategy Selection */}
      {step === 'strategy' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Select a Strategy</h2>
            <button
              onClick={handleBack}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              ← Back
            </button>
          </div>

          {loadingStrategies ? (
            <Spinner />
          ) : (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {strategies.map((strategy, idx) => (
                <button
                  key={strategy.name}
                  onClick={() => handleStrategySelect(strategy)}
                  className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-gray-500">#{idx + 1}</span>
                        <h3 className="font-semibold text-gray-900">{strategy.name}</h3>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{strategy.description}</p>
                      <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-gray-500">
                          Assets: <span className="font-medium text-gray-700">{strategy.assets.join(', ')}</span>
                        </span>
                        <span className="text-gray-500">
                          Sharpe: <span className="font-medium text-gray-700">{strategy.backtest_sharpe.toFixed(2)}</span>
                        </span>
                      </div>
                    </div>
                    <span className="text-primary-600">→</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Asset Selection */}
      {step === 'asset' && selectedStrategy && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Select an Asset</h2>
              <p className="text-sm text-gray-600 mt-1">
                Strategy: <span className="font-medium">{selectedStrategy.name}</span>
              </p>
            </div>
            <button
              onClick={handleBack}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              ← Back
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {selectedStrategy.assets.map((asset) => (
              <button
                key={asset}
                onClick={() => handleAssetSelect(asset)}
                className="p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-center font-semibold text-gray-900"
              >
                {asset}
              </button>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={() => {
                setSelectedAsset('');
                setStep('confirm');
              }}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Skip asset selection (audit entire strategy) →
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Confirmation */}
      {step === 'confirm' && selectedStrategy && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Confirm Audit</h2>
            <button
              onClick={handleBack}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              ← Back
            </button>
          </div>

          <div className="space-y-4 mb-8">
            <div>
              <p className="text-sm text-gray-600">Strategy</p>
              <p className="text-lg font-semibold text-gray-900">{selectedStrategy.name}</p>
              <p className="text-sm text-gray-600 mt-1">{selectedStrategy.description}</p>
            </div>

            <div>
              <p className="text-sm text-gray-600">Assets in Universe</p>
              <p className="text-gray-900">{selectedStrategy.assets.join(', ')}</p>
            </div>

            {selectedAsset && (
              <div className="p-4 bg-primary-50 border border-primary-200 rounded-lg">
                <p className="text-sm text-gray-600">Selected Asset for Focused Audit</p>
                <p className="text-xl font-bold text-primary-700">{selectedAsset}</p>
              </div>
            )}

            {!selectedAsset && (
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <p className="text-sm text-gray-600">Audit Type</p>
                <p className="text-gray-900">Full strategy audit (all assets)</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-4">
              <div>
                <p className="text-sm text-gray-600">Backtest Sharpe</p>
                <p className="text-gray-900 font-semibold">{selectedStrategy.backtest_sharpe.toFixed(2)}</p>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Running Audit...
                </span>
              ) : (
                'Run Audit'
              )}
            </button>

            <button
              type="button"
              onClick={() => navigate('/')}
              disabled={loading}
              className="px-6 py-3 border border-gray-300 rounded-md hover:bg-gray-50 font-medium disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </Container>
  );
}