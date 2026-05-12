import { apiClient } from "@shared/api";
import type {
  DeliveryAddressCreate,
  DeliveryAddressRead,
  DeliveryAddressUpdate,
  MessageResponse,
  UserProfileUpdate,
  UserRead,
  UUID,
} from "@shared/api";

type RequestOptions = {
  signal?: AbortSignal;
};

export const profileApi = {
  createAddress(data: DeliveryAddressCreate): Promise<DeliveryAddressRead> {
    return apiClient.post("/delivery/addresses", data);
  },

  deleteAddress(addressId: UUID): Promise<MessageResponse> {
    return apiClient.delete("/delivery/addresses/{address_id}", {
      pathParams: {
        address_id: addressId,
      },
    });
  },

  deleteAvatar(): Promise<UserRead> {
    return apiClient.delete("/users/me/avatar");
  },

  listAddresses(options?: RequestOptions): Promise<DeliveryAddressRead[]> {
    return apiClient.get("/delivery/addresses", {
      signal: options?.signal,
    });
  },

  updateAddress(addressId: UUID, data: DeliveryAddressUpdate): Promise<DeliveryAddressRead> {
    return apiClient.patch("/delivery/addresses/{address_id}", data, {
      pathParams: {
        address_id: addressId,
      },
    });
  },

  updateProfile(data: UserProfileUpdate): Promise<UserRead> {
    return apiClient.patch("/users/me", data);
  },

  uploadAvatar(file: File): Promise<UserRead> {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post("/users/me/avatar", formData);
  },
};
