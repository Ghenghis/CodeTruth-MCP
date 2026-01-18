/**
 * FIXTURE: No-Op Button
 *
 * This component demonstrates a button that visually exists but causes no effect.
 * The onClick handler is defined but does nothing.
 *
 * EXPECTED FINDING: empty_handler (HIGH severity)
 * EVIDENCE REQUIRED: AST analysis showing empty function body
 */

import React from 'react';

interface Props {
  label: string;
  onSuccess?: () => void;
}

export const NoOpButton: React.FC<Props> = ({ label, onSuccess }) => {
  // Handler is defined but does NOTHING
  const handleClick = () => {
    // Empty - this is the bug!
  };

  // Another no-op: console.log only (debug placeholder)
  const handleSubmit = () => {
    console.log('clicked'); // Does nothing meaningful
  };

  // This handler is NEVER USED
  const handleUnused = () => {
    if (onSuccess) {
      onSuccess();
    }
  };

  return (
    <div className="button-container">
      {/* Button with empty handler - NO-OP */}
      <button onClick={handleClick} className="primary-btn">
        {label}
      </button>

      {/* Button with console-only handler - effectively NO-OP */}
      <button onClick={handleSubmit} className="submit-btn">
        Submit
      </button>

      {/* Button without any handler - also flagged */}
      <button className="orphan-btn">
        Do Something
      </button>
    </div>
  );
};

// Default export that is never imported anywhere
export default NoOpButton;
