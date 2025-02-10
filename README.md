# VDO.Ninja Link Manager

A Python-based application for managing VDO.Ninja video rooms and OBS integration.

## Features

- Generate permanent VDO.Ninja room links
- Mesh-hosted chat rooms
- Password protection
- OBS integration via WebSocket
- Automatic source management
- Debug logging and monitoring
- Save/load room configurations

## Requirements

- Python 3.8+
- OBS Studio 28.0.0+
- OBS WebSocket Plugin 5.0.0+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vidLinker.git
cd vidLinker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

## OBS Integration

The application automatically manages OBS sources using the following naming convention:

- `p0vdosolo`: Host video source
- `p0name`: Host name display
- `p1vdosolo`, `p2vdosolo`, etc.: Player video sources
- `p1name`, `p2name`, etc.: Player name displays

## Room Configuration

1. Set host information:
   - Username
   - Room password
   - API key (optional)

2. Add players:
   - Enter username and character name
   - Generate unique push IDs

3. Configure settings:
   - Resolution (default: 1080p)
   - Mesh hosting
   - Chat display
   - OBS control

## Debug Features

- Comprehensive logging
- Connection status monitoring
- Source creation tracking
- Error reporting with stack traces
- Copy/clear debug information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

For detailed documentation, see [documentation.html](documentation.html).
