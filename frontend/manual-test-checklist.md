# Live Conversation Feature - Manual Testing Checklist

## 🎯 Core Functionality Tests

### Test 1.1: Live Button Activation
- [ ] **Location**: Live button is visible next to Browser icon in mode selector
- [ ] **Label**: Button shows "Live" text and broadcast tower icon
- [ ] **Tooltip**: Hover shows "Live conversation - mindful AI companion"
- [ ] **Click Response**: Clicking activates live conversation mode
- [ ] **State Change**: Button becomes active/highlighted when clicked

### Test 1.2: Overlay Display
- [ ] **Appearance**: Full-screen gradient overlay appears smoothly
- [ ] **Animation**: Fade-in transition works properly (0.5s ease-in-out)
- [ ] **Background**: Gradient from dark blue to purple is visible
- [ ] **Z-index**: Overlay appears above all other content
- [ ] **Backdrop**: Background content is properly covered

### Test 1.3: Particle System Initialization
- [ ] **Canvas Rendering**: Particle canvas appears in center of overlay
- [ ] **Particle Count**: ~100 particles visible in circular formation
- [ ] **Base Animation**: Gentle breathing motion when idle
- [ ] **Circle Size**: 400px x 400px on desktop, 300px on mobile
- [ ] **Visual Effects**: Radial gradient background with blur effect

## 🎛️ User Interface Component Tests

### Test 2.1: Close Button
- [ ] **Position**: X button visible in top-right corner
- [ ] **Styling**: 50px circular button with white icon
- [ ] **Hover Effect**: Button scales to 1.1x and shows hover background
- [ ] **Click Action**: Closes live conversation and returns to main UI
- [ ] **Tooltip**: Shows "Close live conversation" on hover

### Test 2.2: Mute/Unmute Functionality
- [ ] **Default State**: Microphone icon shows unmuted state
- [ ] **Toggle Action**: Click switches between mute/unmute
- [ ] **Visual Feedback**: Icon changes to microphone-slash when muted
- [ ] **Status Update**: Status message updates to show mute state
- [ ] **Audio Stream**: Actual audio track is enabled/disabled

### Test 2.3: Status Messages
- [ ] **Initial Status**: "Connecting..." appears first
- [ ] **Ready State**: Shows "Ready to chat" when connected
- [ ] **Listening State**: "Speak naturally and I'll respond"
- [ ] **Processing State**: "Understanding your message"
- [ ] **Error States**: Clear error messages for failures

### Test 2.4: Responsive Design
- [ ] **Desktop Layout**: 400px particle canvas, proper spacing
- [ ] **Tablet Layout**: Responsive sizing and touch-friendly controls
- [ ] **Mobile Layout**: 300px canvas, adjusted padding (1rem)
- [ ] **Orientation**: Works in both portrait and landscape
- [ ] **Touch Interactions**: All buttons are touch-friendly (min 44px)

## 🎨 Particle Animation System Tests

### Test 3.1: Idle State Animation
- [ ] **Breathing Motion**: Subtle expansion/contraction (±5%)
- [ ] **Particle Movement**: Slow rotation around center
- [ ] **Color**: White particles with gentle glow
- [ ] **Timing**: 2-second breathing cycle
- [ ] **Center Core**: Small white core (6px ± 2px pulse)

### Test 3.2: User Speaking Visuals
- [ ] **Color Change**: Particles turn blue when speaking
- [ ] **Movement**: Particles move inward toward center
- [ ] **Audio Response**: Animation intensity matches voice volume
- [ ] **Core Growth**: Center core grows with audio level (8-18px)
- [ ] **Transition**: Smooth transition from idle state

### Test 3.3: AI Responding Animation
- [ ] **Color Change**: Particles turn orange/amber
- [ ] **Movement**: Particles pulse outward from center
- [ ] **Rhythm**: Regular pulsing motion (not audio-reactive)
- [ ] **Core Effect**: Orange center core with larger size (10px ± 3px)
- [ ] **Status Sync**: Animation matches "AI Speaking" status

### Test 3.4: Audio Level Responsiveness
- [ ] **Threshold Detection**: Animation starts at appropriate volume
- [ ] **Linear Response**: Animation intensity scales with voice level
- [ ] **Noise Filtering**: Background noise doesn't trigger animation
- [ ] **Latency**: Visual feedback appears within 100ms of speaking
- [ ] **Silence Detection**: Animation stops when user stops speaking

## 🔊 Audio Processing Tests

### Test 4.1: Microphone Access
- [ ] **Permission Request**: Browser prompts for microphone access
- [ ] **Grant Flow**: Audio processing starts after permission granted
- [ ] **Deny Flow**: Clear error message if permission denied
- [ ] **Settings**: Works with system default microphone
- [ ] **Device Selection**: Handles multiple audio input devices

### Test 4.2: Audio Context Setup
- [ ] **Initialization**: Web Audio API context created successfully
- [ ] **Sample Rate**: 16kHz audio processing for Gemini Live
- [ ] **Channel Config**: Mono channel (1 channel) configuration
- [ ] **Audio Enhancement**: Echo cancellation and noise suppression enabled
- [ ] **Cross-browser**: Works in Chrome, Firefox, Safari, Edge

### Test 4.3: Voice Activity Detection
- [ ] **Threshold Settings**: Appropriate sensitivity for normal speech
- [ ] **Start Detection**: Accurately detects beginning of speech
- [ ] **End Detection**: Detects when user stops speaking (silence timeout)
- [ ] **Continuous Speech**: Handles long utterances without cutting off
- [ ] **Background Noise**: Filters out ambient noise and breathing

### Test 4.4: Audio Resource Cleanup
- [ ] **Stream Management**: Media stream properly stopped on close
- [ ] **Context Cleanup**: Audio context closed when not needed
- [ ] **Memory Leaks**: No audio processing continues after close
- [ ] **Multiple Sessions**: Can start/stop multiple times without issues
- [ ] **Browser Navigation**: Resources cleaned up on page navigation

## 🌐 WebSocket Integration Tests

### Test 5.1: Connection Establishment
- [ ] **Initial Connection**: "Connecting..." status shown
- [ ] **Authentication**: Ephemeral token requested and used
- [ ] **Gemini Live API**: Connects to correct WSS endpoint
- [ ] **Configuration**: Proper model and voice settings sent
- [ ] **Success Indicator**: "Connected" status after successful setup

### Test 5.2: Message Handling
- [ ] **Audio Transmission**: User speech sent as base64 audio
- [ ] **Response Processing**: AI responses received and parsed
- [ ] **Audio Playback**: AI speech played through speakers
- [ ] **Turn Management**: Proper conversation turn handling
- [ ] **Error Messages**: Clear error handling for API responses

### Test 5.3: Connection Recovery
- [ ] **Disconnect Detection**: Detects when connection is lost
- [ ] **Reconnection Logic**: Automatic reconnection attempts
- [ ] **Exponential Backoff**: Increasing delays between retries
- [ ] **User Notification**: Clear status messages during reconnection
- [ ] **Graceful Degradation**: Handles permanent connection loss

## 📱 Cross-Platform Compatibility Tests

### Test 6.1: Browser Support
- [ ] **Chrome (88+)**: Full feature support
- [ ] **Firefox (84+)**: Audio and WebSocket functionality
- [ ] **Safari (14+)**: WebRTC and getUserMedia support
- [ ] **Edge (88+)**: Complete compatibility
- [ ] **Mobile Browsers**: iOS Safari, Chrome Mobile

### Test 6.2: Operating System Support
- [ ] **Windows 10/11**: Audio permissions and processing
- [ ] **macOS**: System audio access and processing
- [ ] **Linux**: PulseAudio/ALSA compatibility
- [ ] **iOS**: Mobile Safari audio access
- [ ] **Android**: Chrome and Samsung browser support

### Test 6.3: Device Compatibility
- [ ] **Desktop**: Full-size screens and standard microphones
- [ ] **Laptop**: Built-in microphones and webcam arrays
- [ ] **Tablet**: Touch interface and built-in microphones
- [ ] **Smartphone**: Mobile microphones and touch controls
- [ ] **Bluetooth Headsets**: External audio devices

## 🛡️ Error Scenarios and Edge Cases

### Test 7.1: Permission Denied Scenarios
- [ ] **Initial Denial**: Clear error message and retry option
- [ ] **Revoked Permissions**: Handles mid-session permission changes
- [ ] **No Microphone**: Graceful handling of devices without microphone
- [ ] **Audio Conflict**: Handles microphone in use by other apps
- [ ] **User Guidance**: Clear instructions for fixing permission issues

### Test 7.2: Network and API Errors
- [ ] **Network Disconnection**: Handles offline scenarios
- [ ] **API Rate Limits**: Proper error messages for quota exceeded
- [ ] **Invalid Audio**: Handles corrupted or invalid audio data
- [ ] **Server Errors**: Graceful handling of 5xx responses
- [ ] **Timeout Handling**: Appropriate timeouts for all operations

### Test 7.3: Performance Edge Cases
- [ ] **Long Sessions**: Stable during extended conversations
- [ ] **Memory Usage**: No significant memory leaks over time
- [ ] **CPU Usage**: Reasonable processing load during animation
- [ ] **Battery Impact**: Minimal battery drain on mobile devices
- [ ] **Concurrent Tabs**: Handles multiple tabs with audio access

### Test 7.4: Accessibility and Usability
- [ ] **Keyboard Navigation**: All controls accessible via keyboard
- [ ] **Screen Readers**: Proper ARIA labels and descriptions
- [ ] **High Contrast**: Visual elements visible in high contrast mode
- [ ] **Reduced Motion**: Respects prefers-reduced-motion settings
- [ ] **Large Text**: UI scales properly with larger text settings

## 🎭 User Experience Tests

### Test 8.1: Mindful AI Companion Experience
- [ ] **Calming Visuals**: Soothing particle animations and colors
- [ ] **Responsive Feedback**: Immediate visual response to voice
- [ ] **Natural Interaction**: Conversation feels natural and flowing
- [ ] **Emotional Tone**: AI responses are supportive and mindful
- [ ] **Immersive Feel**: Full-screen overlay creates focused environment

### Test 8.2: Performance and Smoothness
- [ ] **Animation Smoothness**: 60fps particle animations
- [ ] **Audio Latency**: <200ms delay from speech to visual feedback
- [ ] **Loading Times**: Quick initialization and connection
- [ ] **Transition Smoothness**: Smooth enter/exit animations
- [ ] **Resource Efficiency**: Minimal impact on system performance

### Test 8.3: Error Recovery and Resilience
- [ ] **Graceful Failures**: No crashes or broken states
- [ ] **Recovery Options**: Clear ways to retry failed operations
- [ ] **User Communication**: Informative error messages
- [ ] **Fallback Behavior**: Degrades gracefully when features unavailable
- [ ] **Retry Mechanisms**: Automatic retry with user option to cancel

## 📊 Test Results Summary

### Overall Assessment
- **Total Tests**: _____ / _____
- **Passed**: _____ (____%)
- **Failed**: _____ (____%)
- **Critical Issues**: _____
- **Recommendations**: _____

### Browser Compatibility Matrix
| Browser | Core Features | Audio | Particles | WebSocket | Overall |
|---------|--------------|-------|-----------|-----------|---------|
| Chrome  |              |       |           |           |         |
| Firefox |              |       |           |           |         |
| Safari  |              |       |           |           |         |
| Edge    |              |       |           |           |         |

### Device Testing Results
| Device Type | Screen Size | Touch | Audio | Performance | Overall |
|-------------|-------------|-------|-------|-------------|---------|
| Desktop     |             |       |       |             |         |
| Laptop      |             |       |       |             |         |
| Tablet      |             |       |       |             |         |
| Mobile      |             |       |       |             |         |

---

**Test Execution Date**: ___________
**Tester**: ___________
**Version**: ___________
**Environment**: ___________