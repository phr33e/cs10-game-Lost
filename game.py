<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Retro Lane Runner</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #111;
            color: #fff;
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }

        h1 {
            margin: 5px 0;
            text-shadow: 0 0 10px #ff0055;
            font-size: 24px;
        }

        #game-container {
            position: relative;
            width: 400px;
            height: 600px;
            border: 4px solid #ff0055;
            box-shadow: 0 0 20px #ff0055;
            background-color: #1a1a1a;
        }

        canvas {
            display: block;
        }

        .overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .btn {
            background: #ff0055;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 18px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            box-shadow: 0 0 10px #ff0055;
            transition: 0.2s;
        }

        .btn:hover {
            background: #ff3377;
            transform: scale(1.05);
        }

        #instructions {
            font-size: 14px;
            color: #aaa;
            margin-top: 10px;
        }
    </style>
</head>
<body>

    <h1>NEON RUNNER</h1>
    <div id="game-container">
        <canvas id="gameCanvas" width="400" height="600"></canvas>

        <div id="start-screen" class="overlay">
            <h2 style="color: #00ffcc; text-shadow: 0 0 10px #00ffcc;">READY RUNNER?</h2>
            <p id="instructions">Avoid obstacles.<br>No jumping. No sliding.<br>Pure reflexes.</p>
            <p style="color: #ffff00; margin: 10px 0;">Controls: A / D or Arrow Keys</p>
            <button class="btn" onclick="startGame()">START</button>
        </div>

        <div id="gameover-screen" class="overlay" style="display: none;">
            <h2 style="color: #ff0055; text-shadow: 0 0 10px #ff0055;">GAME OVER</h2>
            <p id="final-score" style="font-size: 20px;"></p>
            <button class="btn" onclick="startGame()">PLAY AGAIN</button>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const startScreen = document.getElementById('start-screen');
        const gameoverScreen = document.getElementById('gameover-screen');
        const finalScoreText = document.getElementById('final-score');

        // Game Configuration
        const LANE_WIDTH = canvas.width / 3;
        const LANES = [
            LANE_WIDTH / 2,                  // Left Lane Center
            LANE_WIDTH + LANE_WIDTH / 2,     // Middle Lane Center
            LANE_WIDTH * 2 + LANE_WIDTH / 2  // Right Lane Center
        ];

        let gameActive = false;
        let score = 0;
        let speedMultiplier = 1;

        // Player properties
        const player = {
            lane: 1, // Start in the middle (0 = left, 1 = mid, 2 = right)
            x: LANES[1],
            y: 500,
            radius: 20,
            color: '#00ffcc',
            targetX: LANES[1],
            speed: 25 // Snappiness of lane switching
        };

        // Obstacles array
        let obstacles = [];
        let obstacleSpawnTimer = 0;
        let baseSpawnRate = 90; // Frame interval between spawns

        // Track road lines offset for scrolling effect
        let roadOffset = 0;

        // Input Handlers
        window.addEventListener('keydown', (e) => {
            if (!gameActive) return;

            if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
                if (player.lane > 0) {
                    player.lane--;
                    player.targetX = LANES[player.lane];
                }
            }
            if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
                if (player.lane < 2) {
                    player.lane++;
                    player.targetX = LANES[player.lane];
                }
            }
        });

        function startGame() {
            // Reset state
            obstacles = [];
            score = 0;
            speedMultiplier = 1.0;
            player.lane = 1;
            player.x = LANES[1];
            player.targetX = LANES[1];
            obstacleSpawnTimer = 0;

            startScreen.style.display = 'none';
            gameoverScreen.style.display = 'none';
            gameActive = true;

            gameLoop();
        }

        function gameOver() {
            gameActive = false;
            finalScoreText.textContent = `SCORE: ${Math.floor(score)}`;
            gameoverScreen.style.display = 'flex';
        }

        function spawnObstacle() {
            // Pick a random lane
            const laneIndex = Math.floor(Math.random() * 3);

            // Randomize height and color slightly for variety
            obstacles.push({
                lane: laneIndex,
                x: LANES[laneIndex],
                y: -60,
                width: LANE_WIDTH - 40,
                height: 40,
                color: '#ff0055'
            });
        }

        function update() {
            if (!gameActive) return;

            // Increment score over time
            score += 0.15;

            // Gradually increase speed as score goes up
            speedMultiplier = 1 + (score / 300);

            // Interpolate player position for smooth side-to-side transitions
            const dx = player.targetX - player.x;
            player.x += dx * 0.35; // Adjust this factor for faster/slower dash speed

            // Scroll the road lines
            roadOffset += (5 * speedMultiplier);
            if (roadOffset >= 40) {
                roadOffset = 0;
            }

            // Spawn obstacles based on dynamic timer
            obstacleSpawnTimer++;
            const currentSpawnRate = Math.max(35, baseSpawnRate - (score / 15));
            if (obstacleSpawnTimer >= currentSpawnRate) {
                spawnObstacle();
                obstacleSpawnTimer = 0;
            }

            // Update obstacles
            for (let i = obstacles.length - 1; i >= 0; i--) {
                let obs = obstacles[i];
                obs.y += (5 * speedMultiplier);

                // Check Collisions using simple box-to-circle approximation
                const halfWidth = obs.width / 2;
                const closestX = Math.max(obs.x - halfWidth, Math.min(player.x, obs.x + halfWidth));
                const closestY = Math.max(obs.y, Math.min(player.y, obs.y + obs.height));

                const distanceX = player.x - closestX;
                const distanceY = player.y - closestY;
                const distanceSquared = (distanceX * distanceX) + (distanceY * distanceY);

                if (distanceSquared < (player.radius * player.radius)) {
                    gameOver();
                    return;
                }

                // Remove off-screen obstacles
                if (obs.y > canvas.height + 50) {
                    obstacles.splice(i, 1);
                }
            }
        }

        function draw() {
            // Clear Screen
            ctx.fillStyle = '#121212';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw Lane Dividers
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
            ctx.lineWidth = 4;
            ctx.setLineDash([20, 20]);

            // Lane 1 divider
            ctx.beginPath();
            ctx.moveTo(LANE_WIDTH, -roadOffset);
            ctx.lineTo(LANE_WIDTH, canvas.height);
            ctx.stroke();

            // Lane 2 divider
            ctx.beginPath();
            ctx.moveTo(LANE_WIDTH * 2, -roadOffset);
            ctx.lineTo(LANE_WIDTH * 2, canvas.height);
            ctx.stroke();
            ctx.setLineDash([]); // Reset line dash

            // Draw Obstacles
            obstacles.forEach(obs => {
                ctx.fillStyle = obs.color;
                ctx.shadowColor = obs.color;
                ctx.shadowBlur = 15;

                // Draw obstacles as sleek rounded neon rectangles
                ctx.beginPath();
                ctx.roundRect(obs.x - obs.width / 2, obs.y, obs.width, obs.height, 8);
                ctx.fill();
            });

            // Draw Player Ship/Runner (represented as a cool neon triangle)
            ctx.shadowColor = player.color;
            ctx.shadowBlur = 20;
            ctx.fillStyle = player.color;

            ctx.beginPath();
            // Point 1 (Top Tip)
            ctx.moveTo(player.x, player.y - player.radius);
            // Point 2 (Bottom Left)
            ctx.lineTo(player.x - player.radius, player.y + player.radius);
            // Point 3 (Bottom Center Inner fold)
            ctx.lineTo(player.x, player.y + (player.radius / 2));
            // Point 4 (Bottom Right)
            ctx.lineTo(player.x + player.radius, player.y + player.radius);
            ctx.closePath();
            ctx.fill();

            // Reset shadows
            ctx.shadowBlur = 0;

            // Draw Score HUD
            ctx.fillStyle = '#ffff00';
            ctx.font = 'bold 18px "Courier New"';
            ctx.textAlign = 'left';
            ctx.fillText(`SCORE: ${Math.floor(score)}`, 20, 40);

            // Speed multiplier display (arcade style)
            ctx.fillStyle = '#00ffcc';
            ctx.textAlign = 'right';
            ctx.fillText(`x${speedMultiplier.toFixed(1)} SPD`, canvas.width - 20, 40);
        }

        function gameLoop() {
            if (!gameActive) return;

            update();
            draw();
            requestAnimationFrame(gameLoop);
        }
    </script>
</body>
</html>
