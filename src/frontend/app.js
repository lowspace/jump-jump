/**
 * app.js - Main Application for Jump Jump
 * Handles WebSocket connection, game state, and coordinates with UI
 */

class GameClient {
    constructor() {
        this.ui = new GameUI();
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.wsBaseUrl = 'ws://localhost:8000/ws';

        this.init();
    }

    init() {
        // Set up UI callbacks
        this.ui.setInsightCallback((type) => this.useInsight(type));

        // Start game on load
        window.addEventListener('DOMContentLoaded', () => {
            this.startGame();
        });
    }

    // ==================== API Methods ====================

    async startGame() {
        try {
            this.ui.setConnectionStatus('connecting');

            // Check for existing session in URL
            const urlParams = new URLSearchParams(window.location.search);
            const resumeSession = urlParams.get('session');

            // Create or resume game session
            const response = await fetch(`${this.apiBaseUrl}/game/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resume_session_id: resumeSession,
                    start_scene: 'scene-0-wuzhishan',
                    player_role: '少年樵夫'
                })
            });

            if (!response.ok) {
                throw new Error('Failed to start game');
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            // Update URL with session ID
            if (!resumeSession) {
                window.history.replaceState({}, '', `?session=${this.sessionId}`);
            }

            // Update UI with initial state
            this.ui.updateSceneIndicator(data.current_scene);
            this.ui.updateInsightQuota(
                data.insight_quota.true_purpose,
                data.insight_quota.behind_dialogue
            );

            // Display opening narrative
            await this.ui.displayNarrative(data.narrative_text, '', false);

            // Show available actions
            if (data.available_actions) {
                this.ui.showActionButtons(data.available_actions, (action) => this.sendAction(action));
            }

            // Connect WebSocket
            this.connectWebSocket();

        } catch (error) {
            console.error('Error starting game:', error);
            this.ui.setConnectionStatus('disconnected');
            this.ui.displayNarrative('无法连接到游戏服务器，请稍后重试。', '', false);
        }
    }

    async sendAction(action) {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/game/${this.sessionId}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(action)
            });

            if (!response.ok) {
                throw new Error('Action failed');
            }

            const data = await response.json();
            this.handleGameResponse(data);

        } catch (error) {
            console.error('Error sending action:', error);
            this.ui.displayNarrative('操作失败，请重试。', '', false);
        }
    }

    async useInsight(insightType) {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/game/${this.sessionId}/insight`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    insight_type: insightType,
                    target: this.ui.currentNPC || 'current'
                })
            });

            if (!response.ok) {
                throw new Error('Insight failed');
            }

            const data = await response.json();

            if (data.success) {
                this.ui.showInsightResult(data.revealed);
                this.ui.updateInsightQuota(
                    data.quota_remaining.true_purpose,
                    data.quota_remaining.behind_dialogue
                );
            } else {
                alert(data.error || '洞察使用失败');
            }

        } catch (error) {
            console.error('Error using insight:', error);
            alert('洞察使用失败');
        }
    }

    // ==================== WebSocket Methods ====================

    connectWebSocket() {
        if (this.ws) {
            this.ws.close();
        }

        this.ws = new WebSocket(`${this.wsBaseUrl}/${this.sessionId}`);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.ui.setConnectionStatus('connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.ui.setConnectionStatus('disconnected');
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.ui.setConnectionStatus('disconnected');
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
            this.ui.displayNarrative('连接已断开，请刷新页面重试。', '', false);
        }
    }

    sendWebSocketMessage(type, payload) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, payload }));
        }
    }

    // ==================== Message Handlers ====================

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'narrative':
                this.handleNarrative(data.payload);
                break;
            case 'reveal':
                this.handleReveal(data.payload);
                break;
            case 'decision_prompt':
                this.handleDecisionPrompt(data.payload);
                break;
            case 'available_actions':
                this.handleAvailableActions(data.payload);
                break;
            case 'insight_update':
                this.handleInsightUpdate(data.payload);
                break;
            case 'scene_transition':
                this.handleSceneTransition(data.payload);
                break;
            case 'scene_complete':
                this.handleSceneComplete(data.payload);
                break;
            case 'error':
                this.handleError(data.error);
                break;
            case 'pong':
                // Keep-alive response
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleGameResponse(data) {
        // Handle REST API response
        if (data.narrative_text) {
            this.ui.displayNarrative(data.narrative_text, data.emotion_beat);
        }

        if (data.behind_scenes_reveals && data.behind_scenes_reveals.length > 0) {
            this.ui.showBehindScenes(data.behind_scenes_reveals);
        }

        if (data.available_actions) {
            this.ui.showActionButtons(data.available_actions, (action) => this.sendAction(action));
        }

        if (data.insight_quota_remaining) {
            this.ui.updateInsightQuota(
                data.insight_quota_remaining.true_purpose,
                data.insight_quota_remaining.behind_dialogue
            );
        }

        if (data.scene_complete) {
            this.handleSceneComplete(data);
        }
    }

    handleNarrative(payload) {
        this.ui.displayNarrative(payload.text, payload.emotion_beat, payload.typing_effect);
    }

    handleReveal(payload) {
        this.ui.showBehindScenes(payload.reveals);
    }

    handleDecisionPrompt(payload) {
        this.ui.showDecision(
            payload.decision_id,
            '决策',
            payload.description,
            payload.choices,
            (decisionId, choiceId) => {
                this.sendWebSocketMessage('action', {
                    action_type: 'decision',
                    decision_id: decisionId,
                    choice_id: choiceId
                });
            }
        );
    }

    handleAvailableActions(payload) {
        this.ui.showActionButtons(payload, (action) => {
            this.sendWebSocketMessage('action', action);
        });
    }

    handleInsightUpdate(payload) {
        this.ui.updateInsightQuota(payload.true_purpose, payload.behind_dialogue);
    }

    handleSceneTransition(payload) {
        this.ui.showTransitionModal(payload.from, payload.to, payload.transition_text);
        this.ui.updateSceneIndicator(payload.to);
        this.ui.clearNarrative();
    }

    handleSceneComplete(payload) {
        this.ui.displayNarrative('\n=== 场景结束 ===', '', false);
        if (payload.scene_summary) {
            this.ui.displayNarrative(payload.scene_summary, '', false);
        }

        // Show continue button for scene transition
        this.ui.showContinueButton(() => this.transitionToNextScene());
    }

    async transitionToNextScene() {
        try {
            this.ui.displayNarrative('正在进入下一个场景...', '', false);

            const response = await fetch(`${this.apiBaseUrl}/game/${this.sessionId}/transition`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})  // Empty body, let server determine next scene
            });

            if (!response.ok) {
                throw new Error('Scene transition failed');
            }

            const data = await response.json();

            // Hide transition modal
            this.ui.hideTransitionModal();
            this.ui.hideContinueButton();

            // Update UI with new scene
            this.ui.updateSceneIndicator(data.current_scene);
            this.ui.clearNarrative();

            // Display new scene opening
            if (data.narrative_text) {
                await this.ui.displayNarrative(data.narrative_text, '', false);
            }

            // Show new actions
            if (data.available_actions) {
                this.ui.showActionButtons(data.available_actions, (action) => this.sendAction(action));
            }

            // Update insight quota
            if (data.insight_quota) {
                this.ui.updateInsightQuota(
                    data.insight_quota.true_purpose,
                    data.insight_quota.behind_dialogue
                );
            }

        } catch (error) {
            console.error('Error transitioning to next scene:', error);
            this.ui.displayNarrative('场景切换失败，请刷新页面重试。', '', false);
        }
    }

    handleError(error) {
        console.error('Game error:', error);
        this.ui.displayNarrative(`[错误] ${error}`, '', false);
    }

    // ==================== Utility Methods ====================

    ping() {
        this.sendWebSocketMessage('ping', {});
    }

    getState() {
        this.sendWebSocketMessage('get_state', {});
    }
}

// Initialize game client
const gameClient = new GameClient();

// Keep-alive ping
setInterval(() => {
    if (gameClient.ws && gameClient.ws.readyState === WebSocket.OPEN) {
        gameClient.ping();
    }
}, 30000);
