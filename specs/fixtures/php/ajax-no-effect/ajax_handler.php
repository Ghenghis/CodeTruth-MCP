<?php
/**
 * FIXTURE: AJAX No Effect
 *
 * This PHP file demonstrates an AJAX handler that returns success
 * but actually does nothing. Common in Travian/TWLan game servers.
 *
 * EXPECTED FINDING: fake_success_return (CRITICAL severity)
 * EVIDENCE REQUIRED: Static analysis showing no state mutation before success
 */

// Fake authentication check
session_start();

/**
 * Handle building upgrade request
 * PROBLEM: Returns success without actually upgrading anything
 */
function handleBuildingUpgrade() {
    // Validate request
    if (!isset($_POST['building_id']) || !isset($_POST['village_id'])) {
        echo json_encode(['success' => false, 'error' => 'Missing parameters']);
        return;
    }

    $buildingId = (int)$_POST['building_id'];
    $villageId = (int)$_POST['village_id'];

    // Check if user owns village (this part works)
    $userId = $_SESSION['user_id'] ?? 0;
    if (!userOwnsVillage($userId, $villageId)) {
        echo json_encode(['success' => false, 'error' => 'Not your village']);
        return;
    }

    // BUG: No actual upgrade happens!
    // Missing: INSERT INTO building_queue (...)
    // Missing: UPDATE resources SET wood = wood - cost WHERE ...

    // Returns success anyway - FAKE COMPLETENESS
    echo json_encode([
        'success' => true,
        'message' => 'Building upgrade started',
        'building_id' => $buildingId,
        'new_level' => 5  // Hardcoded lie!
    ]);
}

/**
 * Handle troop training request
 * PROBLEM: Same issue - success without effect
 */
function handleTrainTroops() {
    if (!isset($_POST['troop_type']) || !isset($_POST['amount'])) {
        echo json_encode(['success' => false, 'error' => 'Missing parameters']);
        return;
    }

    $troopType = $_POST['troop_type'];
    $amount = (int)$_POST['amount'];

    // Validation exists but...
    if ($amount <= 0 || $amount > 1000) {
        echo json_encode(['success' => false, 'error' => 'Invalid amount']);
        return;
    }

    // BUG: No database operation!
    // Should be: INSERT INTO training_queue (...)
    // Should be: UPDATE resources SET ...

    // Lies to the user
    echo json_encode([
        'success' => true,
        'message' => "Training $amount $troopType",
        'queue_id' => rand(1000, 9999)  // Fake ID!
    ]);
}

// Stub function - also broken
function userOwnsVillage($userId, $villageId) {
    // TODO: Actually check database
    return true;  // Always returns true - security bug!
}

// Route handler
$action = $_GET['action'] ?? '';
switch ($action) {
    case 'upgrade_building':
        handleBuildingUpgrade();
        break;
    case 'train_troops':
        handleTrainTroops();
        break;
    default:
        echo json_encode(['success' => false, 'error' => 'Unknown action']);
}
