/**
 * FIXTURE: Dead Handler
 *
 * This component defines handlers that are never bound to any element.
 * The handlers exist but cannot ever be triggered by user interaction.
 *
 * EXPECTED FINDING: unused_handler (WARNING severity)
 * EVIDENCE REQUIRED: Handler definition without corresponding usage
 */

import React, { useState } from 'react';

interface User {
  id: string;
  name: string;
}

export const DeadHandler: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);

  // DEAD: This handler is defined but NEVER used
  const handleLogin = async (username: string, password: string) => {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    setUser(data.user);
  };

  // DEAD: Also never used
  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

  // DEAD: Complex handler that does real work but is orphaned
  const handleDataExport = async () => {
    const response = await fetch('/api/export');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'export.csv';
    a.click();
  };

  // THIS ONE IS USED
  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div>
      <h1>Welcome {user?.name || 'Guest'}</h1>

      {/* Only handleRefresh is actually bound */}
      <button onClick={handleRefresh}>Refresh</button>

      {/* These buttons reference handlers that DON'T EXIST */}
      <button onClick={() => handleMissing()}>Missing Handler</button>
    </div>
  );
};

// Function that doesn't exist - this will be a runtime error
declare function handleMissing(): void;
