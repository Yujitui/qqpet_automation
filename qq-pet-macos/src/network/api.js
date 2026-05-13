const axios = require("axios");
const auth = require("./auth");

let axiosInstance = null;

function getApiClient() {
  if (axiosInstance) return axiosInstance;

  axiosInstance = axios.create({
    baseURL: auth.getServerUrl(),
    timeout: 10000,
  });

  axiosInstance.interceptors.request.use(
    (config) => {
      const token = auth.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      config.baseURL = auth.getServerUrl();
      return config;
    },
    (error) => Promise.reject(error)
  );

  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        const refreshToken = auth.getRefreshToken();
        if (refreshToken) {
          try {
            const response = await axios.post(
              `${auth.getServerUrl()}/api/auth/refresh`,
              {},
              {
                headers: { Authorization: `Bearer ${refreshToken}` },
              }
            );

            const { access_token: newAccessToken, refresh_token: newRefreshToken } = response.data;
            auth.setTokens(newAccessToken, newRefreshToken);

            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return axiosInstance(originalRequest);
          } catch (refreshError) {
            auth.clearTokens();
            if (global.onAuthRequired) {
              global.onAuthRequired();
            }
            return Promise.reject(refreshError);
          }
        }

        auth.clearTokens();
        if (global.onAuthRequired) {
          global.onAuthRequired();
        }
      }

      return Promise.reject(error);
    }
  );

  return axiosInstance;
}

async function login(username, password) {
  const api = getApiClient();
  const response = await api.post("/api/auth/login", { username, password });
  if (response.status === 201) {
    return { status: "created", message: response.data.message };
  }
  const { access_token, refresh_token, user } = response.data;
  auth.setTokens(access_token, refresh_token, user);
  return { status: "active", access_token, refresh_token, user };
}

async function register(username, password, email = null) {
  const api = getApiClient();
  const response = await api.post("/api/auth/register", { username, password, email });
  return response.data;
}

async function logout() {
  try {
    const api = getApiClient();
    await api.post("/api/auth/logout");
  } catch (e) {
    console.log("Logout API call failed, clearing tokens anyway");
  }
  auth.clearTokens();
}

async function getCurrentUser() {
  const api = getApiClient();
  const response = await api.get("/api/auth/me");
  return response.data;
}

async function changePassword(oldPassword, newPassword) {
  const api = getApiClient();
  const response = await api.post("/api/auth/change-password", {
    old_password: oldPassword,
    new_password: newPassword
  });
  return response.data;
}

async function getPet() {
  const api = getApiClient();
  const response = await api.get("/api/pet");
  return response.data;
}

async function initPet(options = {}) {
  const api = getApiClient();
  const params = {};
  if (options.reset) params.reset = 1;
  if (options.sex) params.sex = options.sex;
  const response = await api.post("/api/pet/init", null, { params });
  return response.data;
}

async function updatePet(data) {
  const api = getApiClient();
  const response = await api.patch("/api/pet", data);
  return response.data;
}

async function getInventory() {
  const api = getApiClient();
  const response = await api.get("/api/pet/inventory");
  return response.data;
}

async function updateInventory(data) {
  const api = getApiClient();
  const response = await api.patch("/api/pet/inventory", data);
  return response.data;
}

module.exports = {
  getApiClient,
  login,
  register,
  logout,
  getCurrentUser,
  changePassword,
  getPet,
  initPet,
  updatePet,
  getInventory,
  updateInventory,
};
