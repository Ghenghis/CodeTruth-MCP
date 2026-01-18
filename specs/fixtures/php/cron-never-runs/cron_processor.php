<?php
/**
 * FIXTURE: Cron Never Runs
 *
 * This PHP file contains cron job logic that is never actually invoked.
 * The crontab entry is missing or misconfigured.
 *
 * EXPECTED FINDING: unreachable_cron (CRITICAL severity)
 * EVIDENCE REQUIRED: No crontab entry found, or entry points to wrong file
 */

define('CRON_SECRET', 'super_secret_key_123');

/**
 * Process building queue - buildings that finished construction
 * PROBLEM: This function exists but cron never calls it
 */
function processBuildingQueue() {
    $db = getDatabase();

    // Find completed buildings
    $query = "SELECT * FROM building_queue WHERE finish_time <= NOW()";
    $result = $db->query($query);

    $processed = 0;
    while ($row = $result->fetch_assoc()) {
        // Update building level
        $db->query("UPDATE buildings SET level = level + 1 WHERE id = " . $row['building_id']);

        // Remove from queue
        $db->query("DELETE FROM building_queue WHERE id = " . $row['id']);

        $processed++;
    }

    logCron("Processed $processed buildings");
    return $processed;
}

/**
 * Process resource generation
 * PROBLEM: Also never runs
 */
function processResourceTick() {
    $db = getDatabase();

    // Calculate time since last tick
    $lastTick = getLastTickTime();
    $hoursPassed = (time() - $lastTick) / 3600;

    if ($hoursPassed < 0.1) {
        return 0; // Too soon
    }

    // Generate resources for all villages
    $query = "UPDATE villages v
              JOIN resource_production rp ON v.id = rp.village_id
              SET v.wood = v.wood + (rp.wood_per_hour * $hoursPassed),
                  v.clay = v.clay + (rp.clay_per_hour * $hoursPassed),
                  v.iron = v.iron + (rp.iron_per_hour * $hoursPassed)";

    $db->query($query);

    setLastTickTime(time());

    logCron("Resource tick processed for " . $hoursPassed . " hours");
    return $hoursPassed;
}

/**
 * Main cron entry point
 * PROBLEM: Nothing calls this file!
 */
function runCron() {
    // Security check
    if (php_sapi_name() !== 'cli') {
        // Web access - check secret
        if (($_GET['secret'] ?? '') !== CRON_SECRET) {
            die('Access denied');
        }
    }

    echo "Starting cron run at " . date('Y-m-d H:i:s') . "\n";

    $buildings = processBuildingQueue();
    $resources = processResourceTick();

    echo "Processed: $buildings buildings, $resources resource ticks\n";
    echo "Cron completed at " . date('Y-m-d H:i:s') . "\n";
}

// Stub functions (would be in includes)
function getDatabase() {
    // This would connect to DB
    return new class {
        public function query($q) { return new class { public function fetch_assoc() { return null; } }; }
    };
}
function getLastTickTime() { return time() - 3600; }
function setLastTickTime($t) { }
function logCron($msg) { error_log("[CRON] $msg"); }

// Entry point - but this file is never executed!
if (basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    runCron();
}
