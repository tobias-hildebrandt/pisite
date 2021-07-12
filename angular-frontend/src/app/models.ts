

export interface Endpoint {
    name: string,
    url: string
}

export interface Response<T> {
    success: boolean,
    message: string,
    data: T | null | {}
}

export interface PowerStatus {
    any_power: boolean,
    statuses: any,
    info: any
}

export interface MinecraftStatus extends PowerStatus {
    any_power: boolean
    statuses: {
        mc_status_ping: boolean,
        process_running: boolean,
        tmux_window_running: boolean
    },
    info: null | {} | {
        motd: string,
        players: string[]
    }
}
