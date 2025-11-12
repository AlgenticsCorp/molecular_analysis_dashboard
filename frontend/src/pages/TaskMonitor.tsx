import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { taskService } from '../services/taskService';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  ClockIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

interface ExecutionStatus {
  execution_id: string;
  task_id: string;
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  external_job_id?: string;
  progress?: number;
  message?: string;
  framework_status?: {
    status: string;
    progress?: number;
    message?: string;
  };
}

const TaskMonitor: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const [pollingEnabled, setPollingEnabled] = useState(true);

  // Poll for status every 5 seconds
  const { data: status, isLoading, error, refetch } = useQuery<ExecutionStatus>({
    queryKey: ['taskStatus', executionId],
    queryFn: () => taskService.getExecutionStatus(executionId!),
    refetchInterval: pollingEnabled ? 5000 : false,
    enabled: !!executionId,
  });

  // Stop polling when task is completed or failed
  useEffect(() => {
    if (status?.status === 'completed' || status?.status === 'failed') {
      setPollingEnabled(false);
    }
  }, [status?.status]);

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-12 w-12 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="h-12 w-12 text-red-500" />;
      case 'running':
        return <ArrowPathIcon className="h-12 w-12 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="h-12 w-12 text-gray-400" />;
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'Completed Successfully';
      case 'failed':
        return 'Execution Failed';
      case 'running':
        return 'Task Running';
      case 'pending':
        return 'Pending Execution';
      default:
        return 'Unknown Status';
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'running':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const calculateDuration = (start?: string, end?: string) => {
    if (!start) return 'N/A';
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const durationMs = endTime - startTime;
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ArrowPathIcon className="h-12 w-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading execution status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <ExclamationCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Status</h2>
          <p className="text-gray-600 mb-4">
            {error instanceof Error ? error.message : 'Unknown error occurred'}
          </p>
          <button
            onClick={() => navigate('/task-library')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Task Library
          </button>
        </div>
      </div>
    );
  }

  const progress = status?.progress ?? (status?.framework_status?.progress);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/task-library')}
            className="text-blue-600 hover:text-blue-700 mb-4 flex items-center"
          >
            <svg className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Task Library
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Task Execution Monitor</h1>
        </div>

        {/* Status Card */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <div className="flex items-center justify-center mb-6">
            {getStatusIcon(status?.status)}
          </div>
          <h2 className={`text-2xl font-semibold text-center mb-2 ${getStatusColor(status?.status)}`}>
            {getStatusText(status?.status)}
          </h2>
          {status?.message && (
            <p className="text-center text-gray-600 mb-4">{status.message}</p>
          )}
          {status?.framework_status?.message && (
            <p className="text-center text-gray-600 mb-4">{status.framework_status.message}</p>
          )}

          {/* Progress Bar */}
          {progress !== undefined && status?.status === 'running' && (
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Execution Details */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Execution Details</h3>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Execution ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{status?.execution_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Task ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{status?.task_id}</dd>
            </div>
            {status?.external_job_id && (
              <div>
                <dt className="text-sm font-medium text-gray-500">External Job ID</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{status.external_job_id}</dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-gray-500">Created At</dt>
              <dd className="mt-1 text-sm text-gray-900">{formatTimestamp(status?.created_at)}</dd>
            </div>
            {status?.started_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Started At</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatTimestamp(status.started_at)}</dd>
              </div>
            )}
            {status?.completed_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Completed At</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatTimestamp(status.completed_at)}</dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-gray-500">Duration</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {calculateDuration(status?.started_at, status?.completed_at)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  status?.status === 'completed' ? 'bg-green-100 text-green-800' :
                  status?.status === 'failed' ? 'bg-red-100 text-red-800' :
                  status?.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {status?.status}
                </span>
              </dd>
            </div>
          </dl>
        </div>

        {/* Error Message */}
        {status?.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-red-900 mb-2">Error Details</h3>
            <p className="text-sm text-red-700">{status.error_message}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          {status?.status === 'completed' && (
            <button
              onClick={() => navigate(`/task-results/${executionId}`)}
              className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
            >
              View Results
            </button>
          )}
          {(status?.status === 'running' || status?.status === 'pending') && (
            <button
              onClick={() => refetch()}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Refresh Status
            </button>
          )}
          {status?.status === 'failed' && (
            <button
              onClick={() => navigate(`/execute-task?task=${status.task_id}`)}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Try Again
            </button>
          )}
        </div>

        {/* Auto-refresh indicator */}
        {pollingEnabled && (
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              <ArrowPathIcon className="inline h-4 w-4 mr-1 animate-spin" />
              Auto-refreshing every 5 seconds...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskMonitor;
