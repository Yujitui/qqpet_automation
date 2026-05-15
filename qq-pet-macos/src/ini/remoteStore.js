const api = require("../network/api");
const auth = require("../network/auth");
const wsClient = require("../network/wsClient");
const Store = require("electron-store");

const localStore = new Store({
  name: "local-config",
  fileExtension: "json",
  clearInvalidConfig: true,
});

let cache = {
  pet: null,
  cache: null,
  sys: null,
  localSettings: null,
};

let isInitialized = false;
let batchTimer = null;
const BATCH_INTERVAL = 1000;

const pendingUpdates = {
  pet: null,
  inventory: null,
};

const camelToSnake = (str) => {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
};

const snakeToCamel = (str) => {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

const convertKeysToCamel = (obj) => {
  if (!obj || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj.map(convertKeysToCamel);
  
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = snakeToCamel(key);
    result[camelKey] = convertKeysToCamel(value);
  }
  return result;
};

const convertKeysToSnake = (obj) => {
  if (!obj || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj.map(convertKeysToSnake);
  
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = camelToSnake(key);
    result[snakeKey] = convertKeysToSnake(value);
  }
  return result;
};

const cleanAndConvertValue = (value, expectedType = null) => {
  if (value === null || value === undefined) {
    return undefined;
  }
  
  if (value === "") {
    if (expectedType === "float") {
      return 0.0;
    }
    if (expectedType === "int" || expectedType === "number") {
      return 0;
    }
    return "";
  }
  
  if (expectedType === "int") {
    if (typeof value === "string") {
      const parsed = parseInt(value, 10);
      return isNaN(parsed) ? 0 : parsed;
    }
    if (typeof value === "number") {
      return Math.floor(value);
    }
  }
  
  if (expectedType === "float") {
    if (typeof value === "string") {
      const parsed = parseFloat(value);
      return isNaN(parsed) ? 0.0 : parsed;
    }
  }
  
  return value;
};

const cleanPetDataForApi = (pet) => {
  if (!pet) return null;
  
  const result = {
    info: {},
    max_info: {},
    active_option: pet.activeOption || {},
    active_value: pet.activeValue || {},
    other_options: pet.otherOptions || {},
    fishing: pet.fishing || {},
  };

  const info = pet.info || {};
  result.info.name = cleanAndConvertValue(info.name, "string") || "";
  result.info.host = cleanAndConvertValue(info.host, "string") || "";
  result.info.sex = cleanAndConvertValue(info.sex, "string") || "GG";
  result.info.growth = cleanAndConvertValue(info.growth, "float");
  result.info.hunger = cleanAndConvertValue(info.hunger, "int");
  result.info.clean = cleanAndConvertValue(info.clean, "int");
  result.info.health = cleanAndConvertValue(info.health, "int");
  result.info.mood = cleanAndConvertValue(info.mood, "int");
  result.info.yb = cleanAndConvertValue(info.yb, "int");
  result.info.intel = cleanAndConvertValue(info.intel, "int");
  result.info.charm = cleanAndConvertValue(info.charm, "int");
  result.info.strong = cleanAndConvertValue(info.strong, "int");
  result.info.birth_day = cleanAndConvertValue(info.birthDay, "string") || "";
  result.info.online_time = cleanAndConvertValue(info.onLineTime, "float");
  result.info.last_login_time = cleanAndConvertValue(info.lastLoginTime, "int");
  result.info.online_data_time = cleanAndConvertValue(info.onlineDataTime, "float");

  const maxInfo = pet.maxInfo || {};
  result.max_info.level = cleanAndConvertValue(maxInfo.level, "int") || 1;
  result.max_info.hunger = cleanAndConvertValue(maxInfo.hunger, "int");
  result.max_info.clean = cleanAndConvertValue(maxInfo.clean, "int");
  result.max_info.mood = cleanAndConvertValue(maxInfo.mood, "int");
  result.max_info.growth_rate = cleanAndConvertValue(maxInfo.growthRate, "int");
  result.max_info.up_growth = cleanAndConvertValue(maxInfo.upGrowth, "int");
  result.max_info.next_growth = cleanAndConvertValue(maxInfo.nextGrowth, "int");
  result.max_info.stop_growth = cleanAndConvertValue(maxInfo.stopGrowth, "bool") || false;

  return result;
};

class RemoteStore {
  constructor() {
    this.isRemoteMode = true;
  }

  async init() {
    if (isInitialized) return;

    try {
      console.log("RemoteStore: Fetching data from server...");
      let petData = await api.getPet().catch((e) => {
        if (e?.response?.status === 404) return null;
        throw e;
      });

      if (!petData) {
        console.log("RemoteStore: No pet data, initializing...");
        try {
          await api.initPet();
          petData = await api.getPet();
        } catch (initErr) {
          console.error("Pet init failed:", initErr?.message);
          throw initErr;
        }
      }

      const [inventoryData] = await Promise.all([
        api.getInventory().catch((e) => { console.log("getInventory failed:", e?.message); return null; }),
      ]);

      console.log("RemoteStore: Data fetched");
      
      cache.pet = this.convertPetToLocal(petData);
      cache.cache = this.convertInventoryToLocal(inventoryData);
      cache.sys = this.loadLocalSettings();
      cache.localSettings = cache.sys;

      isInitialized = true;
      this.isRemoteMode = true;
      console.log("RemoteStore initialized (remote mode)");
    } catch (e) {
      console.log("RemoteStore init failed, switching to local mode:", e);
      this.isRemoteMode = false;
      cache.pet = this.convertPetToLocal(null);
      cache.cache = this.convertInventoryToLocal(null);
      cache.sys = this.loadLocalSettings();
      cache.localSettings = cache.sys;
      isInitialized = true;
      console.log("RemoteStore initialized (local mode fallback)");
    }
  }

  loadLocalSettings() {
    return localStore.get("sys") || {
      doNotDisturb: false,
      startupSelf: false,
      opacity: 1,
      getOption: false,
      focusEnabled: false,
    };
  }

  getLastPosition() {
    return localStore.get("lastPos") || { lastX: 10, lastY: 600 };
  }

  saveLastPosition(x, y) {
    localStore.set("lastPos", { lastX: x, lastY: y });
  }

  convertPetToLocal(apiData) {
    const defaultInfo = {
      name: "",
      host: "",
      sex: "GG",
      growth: 0,
      hunger: 3100,
      clean: 3100,
      health: 5,
      mood: 1000,
      birthDay: "",
      intel: 100,
      charm: 215,
      strong: 123,
      onLineTime: 0,
      yb: 300,
      lastLoginTime: 0,
      onlineDataTime: 0,
    };

    const defaultMaxInfo = {
      stopGrowth: false,
      level: 1,
      upGrowth: 0,
      nextGrowth: 100,
      growthRate: 260,
      hunger: 3100,
      clean: 3100,
      health: 5,
      mood: 1000,
    };

    const lastPos = this.getLastPosition();

    if (!apiData) {
      return {
        info: { ...defaultInfo, lastX: lastPos.lastX, lastY: lastPos.lastY },
        maxInfo: { ...defaultMaxInfo },
        activeOption: { work: null, study: null, trip: null, ill: null, die: null },
        activeValue: { work: {}, study: { chinese: 0, mathematics: 0, politics: 0, music: 0, art: 0, manner: 0, pe: 0, labouring: 0, wushu: 0 } },
        otherOptions: { pinkDiamond: false, growth: 0, growthValue: 0, growthValue_next: 0, pinkDiamondLevel: 0, pinkDiamondBeginDate: 0, pinkDiamondExpirationDate: 0, sweetHeart: false },
        fishing: { fishes: [], harvestfish: 0, allvipcnt: 0, canusecnt: 0, power: 30, needTime: 1 },
        listenMain: {},
      };
    }

    const apiInfo = convertKeysToCamel(apiData.info) || {};
    const apiMaxInfo = convertKeysToCamel(apiData.max_info) || {};

    return {
      info: { ...defaultInfo, ...apiInfo, lastX: lastPos.lastX, lastY: lastPos.lastY },
      maxInfo: { ...defaultMaxInfo, ...apiMaxInfo },
      activeOption: apiData.active_option || { work: null, study: null, trip: null, ill: null, die: null },
      activeValue: apiData.active_value || { work: {}, study: { chinese: 0, mathematics: 0, politics: 0, music: 0, art: 0, manner: 0, pe: 0, labouring: 0, wushu: 0 } },
      otherOptions: apiData.other_options || { pinkDiamond: false, growth: 0, growthValue: 0, growthValue_next: 0, pinkDiamondLevel: 0, pinkDiamondBeginDate: 0, pinkDiamondExpirationDate: 0, sweetHeart: false },
      fishing: apiData.fishing || { fishes: [], harvestfish: 0, allvipcnt: 0, canusecnt: 0, power: 30, needTime: 1 },
      listenMain: {},
    };
  }

  convertInventoryToLocal(apiData) {
    if (!apiData) {
      return {
        store: { food: [], commodity: [], medicine: [], background: [] },
      };
    }
    return {
      store: {
        food: apiData.food || [],
        commodity: apiData.commodity || [],
        medicine: apiData.medicine || [],
        background: apiData.background || [],
      },
    };
  }

  isLocalKey(key) {
    const localOnlyFields = [
      "opacity",
      "doNotDisturb",
      "startupSelf",
      "getOption",
      "focusEnabled",
    ];

    if (key.startsWith("sys.")) {
      const field = key.slice(4);
      if (localOnlyFields.includes(field)) return true;
      if (field.startsWith("focus")) return true;
    }

    return false;
  }

  getItem(key) {
    if (!cache.pet && !cache.cache && !cache.sys) {
      return localStore.get(key) || {};
    }

    const parts = key.split(".");
    const mainKey = parts[0];
    const subKey = parts.slice(1).join(".");

    let value;
    if (mainKey === "pet") {
      value = cache.pet;
    } else if (mainKey === "cache") {
      value = cache.cache;
    } else if (mainKey === "sys") {
      value = cache.sys;
    } else {
      return localStore.get(key) || {};
    }

    if (!value) return {};

    if (!subKey) {
      return value;
    }

    const subParts = subKey.split(".");
    let result = value;
    for (const p of subParts) {
      if (result && typeof result === "object" && p in result) {
        result = result[p];
      } else {
        return {};
      }
    }
    return result;
  }

  saveLocalSettings() {
    if (cache.sys) {
      localStore.set("sys", cache.sys);
    }
  }

  setItem(key, value) {
    const parts = key.split(".");
    const mainKey = parts[0];
    const subKey = parts.slice(1).join(".");

    if (mainKey === "pet") {
      if (!cache.pet) cache.pet = {};
      if (!subKey) {
        cache.pet = { ...cache.pet, ...value };
      } else {
        this.setNestedValue(cache.pet, subKey, value);
      }
      pendingUpdates.pet = cleanPetDataForApi(cache.pet);
      this.scheduleSync();
    } else if (mainKey === "cache") {
      if (!cache.cache) cache.cache = {};
      if (!subKey) {
        cache.cache = { ...cache.cache, ...value };
      } else {
        this.setNestedValue(cache.cache, subKey, value);
      }
      pendingUpdates.inventory = {
        food: cache.cache.store?.food || [],
        commodity: cache.cache.store?.commodity || [],
        medicine: cache.cache.store?.medicine || [],
        background: cache.cache.store?.background || [],
      };
      this.scheduleSync();
    } else if (mainKey === "sys") {
      if (!cache.sys) cache.sys = {};
      if (!subKey) {
        cache.sys = { ...cache.sys, ...value };
      } else {
        this.setNestedValue(cache.sys, subKey, value);
      }
      this.saveLocalSettings();
    } else {
      localStore.set(key, value);
    }
  }

  setNestedValue(obj, path, value) {
    const parts = path.split(".");
    let current = obj;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!(parts[i] in current) || current[parts[i]] === null) {
        current[parts[i]] = {};
      }
      current = current[parts[i]];
    }
    current[parts[parts.length - 1]] = value;
  }

  scheduleSync() {
    if (batchTimer) {
      clearTimeout(batchTimer);
    }
    batchTimer = setTimeout(() => this.syncPending(), BATCH_INTERVAL);
  }

  async syncPending() {
    if (pendingUpdates.pet) {
      const data = pendingUpdates.pet;
      console.log("[syncPending] Syncing pet data via WS...");
      try {
        await wsClient.request("sync.pet", "update", data, 3000);
        pendingUpdates.pet = null;
        console.log("[syncPending] Pet sync via WS succeeded");
      } catch (wsErr) {
        console.log("[syncPending] WS pet sync failed, falling back to HTTP:", wsErr.message);
        try {
          await api.updatePet(data);
          pendingUpdates.pet = null;
          console.log("[syncPending] Pet sync via HTTP succeeded");
        } catch (e) {
          console.log("[syncPending] Pet sync via HTTP also failed:", e.message);
        }
      }
    }

    if (pendingUpdates.inventory) {
      const data = pendingUpdates.inventory;
      console.log("[syncPending] Syncing inventory data via WS...");
      try {
        await wsClient.request("sync.inventory", "update", data, 3000);
        pendingUpdates.inventory = null;
        console.log("[syncPending] Inventory sync via WS succeeded");
      } catch (wsErr) {
        console.log("[syncPending] WS inventory sync failed, falling back to HTTP:", wsErr.message);
        try {
          await api.updateInventory(data);
          pendingUpdates.inventory = null;
          console.log("[syncPending] Inventory sync via HTTP succeeded");
        } catch (e) {
          console.log("[syncPending] Inventory sync via HTTP also failed:", e.message);
        }
      }
    }
  }

  removeItem(key) {
    localStore.delete(key);
    const parts = key.split(".");
    if (parts.length === 1) {
      if (parts[0] === "pet") cache.pet = null;
      else if (parts[0] === "cache") cache.cache = null;
      else if (parts[0] === "sys") cache.sys = null;
    }
  }

  clear() {
    localStore.clear();
    cache = { pet: null, cache: null, sys: null, localSettings: null };
  }

  handleWsPush(msg) {
    const router = msg.router || "";
    const action = msg.action || "";
    const data = msg.data || {};

    if (router === "sync.pet" && action === "update") {
      if (data.info) {
        for (const [key, value] of Object.entries(data.info)) {
          const camelKey = snakeToCamel(key);
          if (cache.pet && cache.pet.info) {
            cache.pet.info[camelKey] = value;
          }
        }
      }
      if (data.max_info) {
        for (const [key, value] of Object.entries(data.max_info)) {
          const camelKey = snakeToCamel(key);
          if (cache.pet && cache.pet.maxInfo) {
            cache.pet.maxInfo[camelKey] = value;
          }
        }
      }
      console.log("[RemoteStore] WS push applied for pet data");
    }

    if (router === "sync.inventory" && action === "update") {
      if (cache.cache && cache.cache.store) {
        if (data.food) cache.cache.store.food = data.food;
        if (data.commodity) cache.cache.store.commodity = data.commodity;
        if (data.medicine) cache.cache.store.medicine = data.medicine;
        if (data.background) cache.cache.store.background = data.background;
      }
      console.log("[RemoteStore] WS push applied for inventory");
    }
  }
}

const remoteStore = new RemoteStore();

module.exports = remoteStore;
