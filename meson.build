project('beta-assistant',
  version: '1.1.0',
  meson_version: '>= 0.59.0',
  default_options: ['warning_level=2']
)

python = import('python')
py_installation = python.find_installation('python3')

prefix = get_option('prefix')
bindir = join_paths(prefix, get_option('bindir'))
datadir = join_paths(prefix, get_option('datadir'))
python_dir = py_installation.get_install_dir()

# Install Python module package
install_subdir('beta_assistant',
  install_dir: python_dir,
  exclude_directories: ['__pycache__']
)

# Install executable wrapper
configure_file(
  input: 'bin/beta-assistant.in',
  output: 'beta-assistant',
  copy: true,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x'
)

# Install Desktop Entry
install_data('desktop/beta-assistant.desktop',
  install_dir: join_paths(datadir, 'applications')
)

# Install Scalable SVG Icon
install_data('desktop/beta-assistant.svg',
  install_dir: join_paths(datadir, 'icons', 'hicolor', 'scalable', 'apps')
)

# Install Rasterized PNG Icons across resolutions
foreach s : ['16', '22', '24', '32', '48', '64', '128', '256', '512']
  install_data('beta_assistant/assets/icons/beta-assistant-' + s + '.png',
    install_dir: join_paths(datadir, 'icons', 'hicolor', s + 'x' + s, 'apps'),
    rename: 'beta-assistant.png'
  )
endforeach
