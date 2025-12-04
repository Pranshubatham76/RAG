import React from 'react';
import { Box, Chip, IconButton, Tooltip } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';

function HealthIndicator({ status, error, onRefresh }) {
  const getStatusInfo = () => {
    if (error) {
      return {
        label: 'Backend Error',
        color: 'error',
        icon: <ErrorIcon />,
      };
    }

    if (!status) {
      return {
        label: 'Checking...',
        color: 'default',
        icon: <WarningIcon />,
      };
    }

    if (status.status === 'healthy' && status.ready) {
      return {
        label: `Ready (${status.vector_store?.count || 0} chunks)`,
        color: 'success',
        icon: <CheckCircleIcon />,
      };
    }

    if (status.status === 'healthy' && !status.ready) {
      return {
        label: 'Not Ready',
        color: 'warning',
        icon: <WarningIcon />,
      };
    }

    return {
      label: 'Unhealthy',
      color: 'error',
      icon: <ErrorIcon />,
    };
  };

  const statusInfo = getStatusInfo();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Chip
        icon={statusInfo.icon}
        label={statusInfo.label}
        color={statusInfo.color}
        size="small"
      />
      <Tooltip title="Refresh health status">
        <IconButton size="small" onClick={onRefresh}>
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

export default HealthIndicator;
