import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:just_audio/just_audio.dart';
import 'package:audio_session/audio_session.dart';

class TestAudioScreen extends StatefulWidget {
  const TestAudioScreen({super.key});

  @override
  State<TestAudioScreen> createState() => _TestAudioScreenState();
}

class _TestAudioScreenState extends State<TestAudioScreen> {
  final AudioPlayer _player = AudioPlayer();
  String _status = 'Ready';

  @override
  void initState() {
    super.initState();
    _initAudioSession();
  }

  Future<void> _initAudioSession() async {
    try {
      final session = await AudioSession.instance;
      await session.configure(const AudioSessionConfiguration.music());
      print('Audio session configured');
      setState(() {
        _status = 'Audio session ready';
      });
    } catch (e) {
      print('Error configuring audio session: $e');
      setState(() {
        _status = 'Session error: $e';
      });
    }
  }

  Future<void> _checkAssetExists() async {
    setState(() {
      _status = 'Checking if asset exists...';
    });

    try {
      final data = await rootBundle.load('assets/stories/N5_G0_001/audio/full_story_slow.mp3');
      print('Asset exists! Size: ${data.lengthInBytes} bytes');
      setState(() {
        _status = 'Asset EXISTS! Size: ${data.lengthInBytes} bytes';
      });
    } catch (e) {
      print('Asset does not exist: $e');
      setState(() {
        _status = 'Asset NOT FOUND: $e';
      });
    }
  }

  Future<void> _testNetworkAudio() async {
    setState(() {
      _status = 'Testing network audio...';
    });

    try {
      print('Testing network audio...');
      await _player.setUrl('https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3');
      
      setState(() {
        _status = 'Network audio loaded! Duration: ${_player.duration}';
      });
      
      await _player.play();
      
      setState(() {
        _status = 'Network audio playing!';
      });
      
      print('Network audio success!');
    } catch (e) {
      print('Network audio error: $e');
      setState(() {
        _status = 'Network error: $e';
      });
    }
  }

  Future<void> _testAssetAudio() async {
    setState(() {
      _status = 'Testing asset audio...';
    });

    try {
      print('Step 1: Setting asset...');
      await _player.setAsset('assets/stories/N5_G0_001/audio/full_story_slow.mp3');
      
      setState(() {
        _status = 'Asset loaded! Duration: ${_player.duration}';
      });
      
      print('Step 2: Playing...');
      await _player.play();
      
      setState(() {
        _status = 'Asset playing!';
      });
      
      print('Step 3: Success!');
    } catch (e) {
      print('Asset error: $e');
      setState(() {
        _status = 'Asset error: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Audio Test')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(_status, textAlign: TextAlign.center),
            ),
            const SizedBox(height: 20),
            
            ElevatedButton(
              onPressed: _checkAssetExists,
              child: const Text('Check Asset Exists'),
            ),
            const SizedBox(height: 10),
            
            ElevatedButton(
              onPressed: _testNetworkAudio,
              child: const Text('Test Network Audio'),
            ),
            const SizedBox(height: 10),
            
            ElevatedButton(
              onPressed: _testAssetAudio,
              child: const Text('Test Asset Audio'),
            ),
            const SizedBox(height: 10),
            
            ElevatedButton(
              onPressed: () {
                _player.stop();
                setState(() {
                  _status = 'Stopped';
                });
              },
              child: const Text('Stop'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}