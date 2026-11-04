/**
 * Production mock dataset for catalog, categories, inventory, and initial user addresses.
 * Provides high-fidelity fallback when any microservice is offline or initializing.
 */

export const MOCK_CATEGORIES = [
  { uuid: 'cat-comp-01', name: 'Laptops & Workstations', slug: 'laptops-workstations', description: 'Cutting edge computing workstations' },
  { uuid: 'cat-audio-02', name: 'Audio & Acoustics', slug: 'audio-acoustics', description: 'Studio grade ANC headphones and speakers' },
  { uuid: 'cat-disp-03', name: 'Monitors & Displays', slug: 'monitors-displays', description: 'Color accurate 4K and 5K pro creator displays' },
  { uuid: 'cat-periph-04', name: 'Mechanical Keyboards & Gear', slug: 'keyboards-gear', description: 'Custom CNC mechanical keyboards and peripherals' },
  { uuid: 'cat-iot-05', name: 'Smart Home & Power', slug: 'smart-home-power', description: 'High wattage GaN chargers and smart IoT accessories' },
];

export const MOCK_PRODUCTS = [
  {
    uuid: 'prod-macbook-m3',
    sku: 'MACBOOK-M3-MAX',
    name: 'Apple MacBook Pro 16" M3 Max',
    slug: 'macbook-pro-16-m3-max',
    category_uuid: 'cat-comp-01',
    category_name: 'Laptops & Workstations',
    price: 3499.00,
    currency: 'USD',
    is_active: true,
    rating: 4.9,
    reviewsCount: 128,
    badge: 'Flagship',
    image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&auto=format&fit=crop&q=80',
    description: 'Apple M3 Max chip with 16-core CPU, 40-core GPU, 48GB unified memory, and 1TB ultra-fast SSD storage. Liquid Retina XDR display with ProMotion.',
    features: ['16-Core CPU & 40-Core GPU', '48GB Unified Memory', '1TB NVMe PCIe 4.0 Storage', 'Up to 22 Hours Battery Life'],
    inventory: {
      available_quantity: 42,
      warehouse_location: 'SAN-FRANCISCO-HUB',
      status: 'IN_STOCK'
    }
  },
  {
    uuid: 'prod-dell-xps-16',
    sku: 'DELL-XPS-16-9640',
    name: 'Dell XPS 16 OLED Workstation',
    slug: 'dell-xps-16-oled',
    category_uuid: 'cat-comp-01',
    category_name: 'Laptops & Workstations',
    price: 2699.00,
    currency: 'USD',
    is_active: true,
    rating: 4.7,
    reviewsCount: 84,
    badge: 'Popular',
    image: 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&auto=format&fit=crop&q=80',
    description: 'Intel Core Ultra 9 185H processor, NVIDIA GeForce RTX 4070 Laptop GPU, 32GB LPDDR5x RAM, 4K+ InfinityEdge OLED Touch display.',
    features: ['Intel Core Ultra 9 with AI Boost', 'RTX 4070 8GB GDDR6', '3.2K 120Hz Touch OLED Display', 'CNC Machined Aluminum'],
    inventory: {
      available_quantity: 18,
      warehouse_location: 'NEW-YORK-HUB',
      status: 'IN_STOCK'
    }
  },
  {
    uuid: 'prod-sony-wh1000xm5',
    sku: 'SONY-WH1000XM5-BLK',
    name: 'Sony WH-1000XM5 Noise Canceling Headphones',
    slug: 'sony-wh-1000xm5',
    category_uuid: 'cat-audio-02',
    category_name: 'Audio & Acoustics',
    price: 399.99,
    currency: 'USD',
    is_active: true,
    rating: 4.8,
    reviewsCount: 312,
    badge: 'Best Seller',
    image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
    description: 'Industry-leading noise canceling with two processors and 8 microphones. Hi-Res Audio wireless with LDAC, crystal clear hands-free calling, and 30hr battery.',
    features: ['Dual HD Noise Cancelling QN1 Processor', 'Auto NC Optimizer', 'Up to 30 Hours Playback', 'Multipoint Bluetooth 5.2'],
    inventory: {
      available_quantity: 65,
      warehouse_location: 'AUSTIN-HUB',
      status: 'IN_STOCK'
    }
  },
  {
    uuid: 'prod-apple-studio-disp',
    sku: 'APPLE-STUDIO-DISP-5K',
    name: 'Apple Studio Display 27" 5K Retina',
    slug: 'apple-studio-display-5k',
    category_uuid: 'cat-disp-03',
    category_name: 'Monitors & Displays',
    price: 1599.00,
    currency: 'USD',
    is_active: true,
    rating: 4.9,
    reviewsCount: 67,
    badge: 'Pro Choice',
    image: 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&auto=format&fit=crop&q=80',
    description: 'Immersive 27-inch 5K Retina display with 600 nits of brightness, P3 wide color gamut, 12MP Ultra Wide camera with Center Stage, and studio-quality 6-speaker array.',
    features: ['5120-by-2880 Resolution at 218 ppi', '12MP Ultra Wide Camera w/ Center Stage', 'Six-Speaker Sound System with Spatial Audio', '96W Host Charging over Thunderbolt 3'],
    inventory: {
      available_quantity: 12,
      warehouse_location: 'SAN-FRANCISCO-HUB',
      status: 'LOW_STOCK'
    }
  },
  {
    uuid: 'prod-samsung-odyssey-g9',
    sku: 'SAM-ODYSSEY-G9-49',
    name: 'Samsung Odyssey OLED G9 49" Curved Gaming Monitor',
    slug: 'samsung-odyssey-oled-g9',
    category_uuid: 'cat-disp-03',
    category_name: 'Monitors & Displays',
    price: 1799.99,
    currency: 'USD',
    is_active: true,
    rating: 4.8,
    reviewsCount: 95,
    badge: 'Ultra-Wide',
    image: 'https://images.unsplash.com/photo-1547082299-de196ea013d6?w=800&auto=format&fit=crop&q=80',
    description: 'Dual QHD OLED screen with 0.03ms response time and 240Hz refresh rate. 1800R curved gaming masterpiece with Neo Quantum Processor Pro.',
    features: ['49" Dual QHD (5120 x 1440)', '240Hz Refresh Rate & 0.03ms Response', 'DisplayHDR True Black 400', 'AMD FreeSync Premium Pro'],
    inventory: {
      available_quantity: 8,
      warehouse_location: 'SEATTLE-HUB',
      status: 'LOW_STOCK'
    }
  },
  {
    uuid: 'prod-keychron-q1-pro',
    sku: 'KEYCHRON-Q1-PRO-MAX',
    name: 'Keychron Q1 Pro Wireless Custom Mechanical Keyboard',
    slug: 'keychron-q1-pro',
    category_uuid: 'cat-periph-04',
    category_name: 'Mechanical Keyboards & Gear',
    price: 199.00,
    currency: 'USD',
    is_active: true,
    rating: 4.9,
    reviewsCount: 156,
    badge: 'Community Favorite',
    image: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&auto=format&fit=crop&q=80',
    description: 'Full CNC machined 6063 aluminum body, double-gasket design, QMK/VIA programmable keymaps, hot-swappable switches, and seamless Bluetooth 5.1.',
    features: ['CNC Anodized Aluminum Chassis', 'Double-Gasket Acoustic Dampening', 'QMK / VIA Remapping Support', 'Hot-Swappable Gateron Jupiter Switches'],
    inventory: {
      available_quantity: 54,
      warehouse_location: 'AUSTIN-HUB',
      status: 'IN_STOCK'
    }
  },
  {
    uuid: 'prod-logi-mx-master-3s',
    sku: 'LOGI-MX-MASTER-3S',
    name: 'Logitech MX Master 3S Wireless Performance Mouse',
    slug: 'logitech-mx-master-3s',
    category_uuid: 'cat-periph-04',
    category_name: 'Mechanical Keyboards & Gear',
    price: 99.99,
    currency: 'USD',
    is_active: true,
    rating: 4.9,
    reviewsCount: 520,
    badge: 'Best Seller',
    image: 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800&auto=format&fit=crop&q=80',
    description: 'Quiet Clicks with 8K DPI tracking on any surface, MagSpeed electromagnetic scrolling wheel, ergonomic thumb cradle, and cross-computer Flow control.',
    features: ['8000 DPI Darkfield Optical Sensor', 'MagSpeed Electromagnetic Wheel (1000 lines/sec)', 'Quiet Click Switches (90% noise reduction)', 'USB-C Quick Recharge (70 days per charge)'],
    inventory: {
      available_quantity: 88,
      warehouse_location: 'CHICAGO-HUB',
      status: 'IN_STOCK'
    }
  },
  {
    uuid: 'prod-anker-prime-27k',
    sku: 'ANKER-PRIME-27650',
    name: 'Anker Prime 27,650mAh Power Bank (250W GaN)',
    slug: 'anker-prime-powerbank-250w',
    category_uuid: 'cat-iot-05',
    category_name: 'Smart Home & Power',
    price: 179.99,
    currency: 'USD',
    is_active: true,
    rating: 4.8,
    reviewsCount: 78,
    badge: 'High Power',
    image: 'https://images.unsplash.com/photo-1609592424368-8a0a9db69e5d?w=800&auto=format&fit=crop&q=80',
    description: 'Fast-charges two laptops simultaneously with up to 140W per USB-C port (250W multi-device total). Real-time smart digital display with companion app telemetry.',
    features: ['250W Maximum Multi-Port GaN Output', '27,650mAh Airline-Safe Capacity', 'Smart Color Display with Real-time Wattage Stats', '170W Ultra-Fast Self Recharging in 37 mins'],
    inventory: {
      available_quantity: 35,
      warehouse_location: 'SAN-FRANCISCO-HUB',
      status: 'IN_STOCK'
    }
  },
  {
    uuid: 'prod-elgato-stream-deck',
    sku: 'ELGATO-STREAM-DECK-MK2',
    name: 'Elgato Stream Deck MK.2 Studio Controller',
    slug: 'elgato-stream-deck-mk2',
    category_uuid: 'cat-periph-04',
    category_name: 'Mechanical Keyboards & Gear',
    price: 149.99,
    currency: 'USD',
    is_active: true,
    rating: 4.7,
    reviewsCount: 110,
    badge: 'Creator Essential',
    image: 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=800&auto=format&fit=crop&q=80',
    description: '15 customizable LCD keys to control apps, tools, and platforms. One-touch tactical operation with detachable faceplates and USB-C cable.',
    features: ['15 Custom LCD Visual Keys', 'Direct OBS, Twitch, Spotify, Discord Integration', 'Multi-Action Hotkey Macro Sequencing', 'Interchangeable Faceplates'],
    inventory: {
      available_quantity: 4,
      warehouse_location: 'NEW-YORK-HUB',
      status: 'LOW_STOCK'
    }
  }
];

export const MOCK_SAVED_ADDRESSES = [
  {
    uuid: 'addr-hq-sf-01',
    address_line_1: '500 Howard Street, Suite 400',
    address_line_2: 'Technology Tower',
    city: 'San Francisco',
    state: 'CA',
    postal_code: '94105',
    country: 'United States',
    is_default: true,
  },
  {
    uuid: 'addr-res-ny-02',
    address_line_1: '250 Hudson Street, Apt 12B',
    address_line_2: '',
    city: 'New York',
    state: 'NY',
    postal_code: '10013',
    country: 'United States',
    is_default: false,
  }
];

